"""
大盘指数服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date
import pandas as pd

from app.models.index import IndexHistory
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class IndexService:
    """大盘指数服务类"""
    
    @staticmethod
    def get_index_list(
        db: Session,
        target_date: date,
        index_code: Optional[str] = None
    ) -> List[IndexHistory]:
        """获取指数列表，包含成交量变化比例"""
        from datetime import timedelta
        from sqlalchemy import desc
        
        query = db.query(IndexHistory).filter(IndexHistory.date == target_date)
        
        if index_code:
            query = query.filter(IndexHistory.index_code == index_code)
        
        indices = query.all()
        
        # 批量查询前一交易日数据以提高效率
        if indices:
            index_codes = [idx.index_code for idx in indices]
            # 查找前一个交易日的数据（最多往前找5个交易日）
            prev_indices_map = {}
            for i in range(1, 6):
                check_date = target_date - timedelta(days=i)
                prev_indices = db.query(IndexHistory).filter(
                    IndexHistory.index_code.in_(index_codes),
                    IndexHistory.date == check_date
                ).all()
                for prev_idx in prev_indices:
                    if prev_idx.index_code not in prev_indices_map and prev_idx.volume:
                        prev_indices_map[prev_idx.index_code] = prev_idx
                if len(prev_indices_map) == len(index_codes):
                    break  # 所有指数都找到了前一交易日数据
        
        # 计算成交量变化比例
        for index in indices:
            if index.volume and index.index_code in prev_indices_map:
                prev_index = prev_indices_map[index.index_code]
                if prev_index.volume:
                    # 计算变化比例: (当前成交量 - 前一交易日成交量) / 前一交易日成交量 * 100
                    volume_change_percent = ((index.volume - prev_index.volume) / prev_index.volume) * 100
                    # 将计算结果存储到对象的临时属性中
                    index.volume_change_percent = round(volume_change_percent, 2)
                else:
                    index.volume_change_percent = None
            else:
                index.volume_change_percent = None
        
        return indices
    
    @staticmethod
    def get_index_history(
        db: Session,
        index_code: str,
        start_date: date,
        end_date: date
    ) -> List[IndexHistory]:
        """获取指数历史数据"""
        return db.query(IndexHistory).filter(
            and_(
                IndexHistory.index_code == index_code,
                IndexHistory.date >= start_date,
                IndexHistory.date <= end_date
            )
        ).order_by(IndexHistory.date).all()
    
    @staticmethod
    def save_index_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """保存指数数据"""
        count = 0
        for _, row in df.iterrows():
            # stock_zh_index_spot_em 返回的字段名可能不同，需要根据实际返回调整
            index_code = str(row.get("代码", row.get("index_code", "")))
            index_name = row.get("名称", row.get("name", ""))
            
            if not index_code or not index_name:
                continue
            
            existing = db.query(IndexHistory).filter(
                and_(
                    IndexHistory.date == target_date,
                    IndexHistory.index_code == index_code
                )
            ).first()
            
            # 尝试多种可能的字段名
            close_price = row.get("最新价", row.get("最新", row.get("close", None)))
            change_percent = row.get("涨跌幅", row.get("涨跌", row.get("change_pct", None)))
            volume = row.get("成交量", row.get("volume", None))
            amount = row.get("成交额", row.get("amount", None))
            
            if existing:
                existing.index_name = index_name
                if close_price is not None:
                    existing.close_price = close_price
                if change_percent is not None:
                    existing.change_percent = change_percent
                if volume is not None:
                    existing.volume = volume
                if amount is not None:
                    existing.amount = amount
            else:
                index = IndexHistory(
                    date=target_date,
                    index_code=index_code,
                    index_name=index_name,
                    close_price=close_price,
                    change_percent=change_percent,
                    volume=volume,
                    amount=amount,
                )
                db.add(index)
            
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date):
        """
        同步大盘指数数据
        从AKShare获取数据并保存到数据库
        使用接口: stock_zh_index_spot_em
        """
        from app.utils.sync_result import SyncResult
        
        try:
            # 获取所有A股指数的实时行情数据
            df = safe_akshare_call(ak.stock_zh_index_spot_em)
            
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的指数数据，接口返回空或网络异常"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")
            
            # 保存数据
            count = IndexService.save_index_data(db, target_date, df)
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的指数数据，共 {count} 条")
            return SyncResult.success_result(f"指数数据同步成功", count)
        except Exception as e:
            error_msg = f"同步指数数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)

