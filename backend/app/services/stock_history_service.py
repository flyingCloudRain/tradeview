"""
股票历史行情服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import Optional, List
from datetime import date, timedelta
import pandas as pd

from app.models.stock_history import StockHistory
from app.models.limit_up_board import LimitUpBoard
from app.utils.akshare_utils import safe_akshare_call
from app.utils.sync_result import SyncResult
from app.utils.format_utils import safe_float, safe_int
import akshare as ak


class StockHistoryService:
    """股票历史行情服务类"""
    
    @staticmethod
    def normalize_stock_code(stock_code: str) -> str:
        """
        标准化股票代码格式
        将 "002729.SZ" 转换为 "002729"
        """
        if not stock_code:
            return stock_code
        
        # 移除后缀（.SZ, .SH, .BJ 等）
        code = stock_code.split('.')[0]
        
        # 确保是6位数字
        return code.zfill(6)
    
    @staticmethod
    def sync_limit_up_stocks_history(
        db: Session,
        target_date: Optional[date] = None,
        months: int = 3
    ) -> SyncResult:
        """
        同步涨停股的历史行情数据（3个月）
        
        Args:
            db: 数据库会话
            target_date: 目标日期，None表示使用当前日期
            months: 获取历史数据的月数，默认3个月
        
        Returns:
            SyncResult: 同步结果
        """
        try:
            if target_date is None:
                target_date = date.today()
            
            print(f"开始同步涨停股历史行情数据，目标日期: {target_date}, 历史月数: {months}")
            
            # 获取目标日期的所有涨停股
            limit_up_stocks = db.query(LimitUpBoard).filter(
                LimitUpBoard.date == target_date
            ).all()
            
            if not limit_up_stocks:
                print(f"目标日期 {target_date} 没有涨停股数据")
                return SyncResult.failure_result(
                    f"目标日期 {target_date} 没有涨停股数据",
                    "无数据源"
                )
            
            # 去重股票代码
            stock_codes = list(set([stock.stock_code for stock in limit_up_stocks]))
            print(f"找到 {len(stock_codes)} 只涨停股，开始同步历史数据...")
            
            # 计算日期范围
            end_date = target_date
            start_date = end_date - timedelta(days=months * 30)  # 大约3个月
            
            start_date_str = start_date.strftime("%Y%m%d")
            end_date_str = end_date.strftime("%Y%m%d")
            
            success_count = 0
            fail_count = 0
            total_records = 0
            
            for idx, stock_code in enumerate(stock_codes, 1):
                try:
                    # 标准化股票代码格式（移除 .SZ/.SH/.BJ 后缀）
                    normalized_code = StockHistoryService.normalize_stock_code(stock_code)
                    print(f"[{idx}/{len(stock_codes)}] 同步 {stock_code} ({normalized_code}) 的历史数据...")
                    
                    # 调用 akshare 接口获取历史数据
                    df = safe_akshare_call(
                        ak.stock_zh_a_hist,
                        symbol=normalized_code,
                        period="daily",
                        start_date=start_date_str,
                        end_date=end_date_str,
                        adjust=""  # 不复权
                    )
                    
                    if df is None or df.empty:
                        print(f"  ⚠️ {stock_code} 无历史数据")
                        fail_count += 1
                        continue
                    
                    # 保存数据
                    saved_count = StockHistoryService.save_stock_history(
                        db, stock_code, df
                    )
                    
                    if saved_count > 0:
                        success_count += 1
                        total_records += saved_count
                        print(f"  ✅ {stock_code} 成功保存 {saved_count} 条记录")
                    else:
                        fail_count += 1
                        print(f"  ❌ {stock_code} 保存失败")
                    
                except Exception as e:
                    print(f"  ❌ {stock_code} 同步异常: {str(e)}")
                    fail_count += 1
                    import traceback
                    traceback.print_exc()
            
            print(f"\n同步完成: 成功 {success_count}/{len(stock_codes)}, 失败 {fail_count}, 总记录数 {total_records}")
            
            if success_count == 0:
                return SyncResult.failure_result(
                    "所有股票同步失败",
                    f"成功: {success_count}, 失败: {fail_count}"
                )
            
            return SyncResult.success_result(
                f"同步完成: 成功 {success_count}/{len(stock_codes)} 只股票，共 {total_records} 条记录",
                total_records
            )
            
        except Exception as e:
            error_msg = f"同步涨停股历史行情数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)
    
    @staticmethod
    def save_stock_history(
        db: Session,
        stock_code: str,
        df: pd.DataFrame
    ) -> int:
        """
        保存股票历史行情数据
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            df: 历史行情数据DataFrame
        
        Returns:
            int: 保存的记录数
        """
        if df is None or df.empty:
            return 0
        
        # 标准化列名映射（根据 akshare 返回的列名）
        column_mapping = {
            "日期": "date",
            "股票代码": "stock_code",
            "开盘": "open_price",
            "收盘": "close_price",
            "最高": "high_price",
            "最低": "low_price",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "change_percent",
            "涨跌额": "change_amount",
            "换手率": "turnover_rate",
        }
        
        # 重命名列
        df = df.rename(columns=column_mapping)
        
        saved_count = 0
        
        for _, row in df.iterrows():
            try:
                # 解析日期
                trade_date = pd.to_datetime(row.get("date")).date()
                
                # 检查是否已存在
                existing = db.query(StockHistory).filter(
                    and_(
                        StockHistory.date == trade_date,
                        StockHistory.stock_code == stock_code
                    )
                ).first()
                
                if existing:
                    # 更新现有记录
                    existing.stock_name = row.get("stock_name") or existing.stock_name
                    existing.open_price = safe_float(row.get("open_price"))
                    existing.close_price = safe_float(row.get("close_price"))
                    existing.high_price = safe_float(row.get("high_price"))
                    existing.low_price = safe_float(row.get("low_price"))
                    existing.volume = safe_int(row.get("volume"))
                    existing.amount = safe_float(row.get("amount"))
                    existing.amplitude = safe_float(row.get("amplitude"))
                    existing.change_percent = safe_float(row.get("change_percent"))
                    existing.change_amount = safe_float(row.get("change_amount"))
                    existing.turnover_rate = safe_float(row.get("turnover_rate"))
                else:
                    # 创建新记录
                    history = StockHistory(
                        date=trade_date,
                        stock_code=stock_code,
                        stock_name=row.get("stock_name"),
                        open_price=safe_float(row.get("open_price")),
                        close_price=safe_float(row.get("close_price")),
                        high_price=safe_float(row.get("high_price")),
                        low_price=safe_float(row.get("low_price")),
                        volume=safe_int(row.get("volume")),
                        amount=safe_float(row.get("amount")),
                        amplitude=safe_float(row.get("amplitude")),
                        change_percent=safe_float(row.get("change_percent")),
                        change_amount=safe_float(row.get("change_amount")),
                        turnover_rate=safe_float(row.get("turnover_rate")),
                    )
                    db.add(history)
                
                saved_count += 1
                
            except Exception as e:
                print(f"  保存单条记录失败: {str(e)}")
                continue
        
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"  提交失败: {str(e)}")
            return 0
        
        return saved_count
    
    @staticmethod
    def get_stock_history(
        db: Session,
        stock_code: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[StockHistory]:
        """
        获取股票历史行情数据
        
        Args:
            db: 数据库会话
            stock_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            List[StockHistory]: 历史行情数据列表
        """
        query = db.query(StockHistory).filter(
            StockHistory.stock_code == stock_code
        )
        
        if start_date:
            query = query.filter(StockHistory.date >= start_date)
        
        if end_date:
            query = query.filter(StockHistory.date <= end_date)
        
        return query.order_by(desc(StockHistory.date)).all()
