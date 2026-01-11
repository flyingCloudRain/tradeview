"""
资金流服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date
import pandas as pd

from app.models.fund_flow import StockFundFlow, IndustryFundFlow, ConceptFundFlow
from app.models.zt_pool import ZtPool
from app.models.lhb import LhbDetail
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


class FundFlowService:
    """资金流服务类"""
    
    @staticmethod
    def update_flags_for_date_range(
        db: Session,
        start_date: date,
        end_date: date,
        batch_size: int = 1000
    ) -> dict:
        """
        批量更新指定日期范围内的资金流标志（涨停、龙虎榜）
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            batch_size: 每批处理的记录数
            
        Returns:
            dict: 更新统计信息
        """
        from sqlalchemy import func
        
        # 查询需要更新的记录
        query = db.query(StockFundFlow).filter(
            and_(
                StockFundFlow.date >= start_date,
                StockFundFlow.date <= end_date
            )
        )
        
        total_count = query.count()
        updated_limit_up = 0
        updated_lhb = 0
        processed = 0
        
        offset = 0
        while offset < total_count:
            records = query.offset(offset).limit(batch_size).all()
            
            if not records:
                break
            
            for record in records:
                # 查询是否涨停
                is_limit_up = db.query(ZtPool).filter(
                    and_(
                        ZtPool.date == record.date,
                        ZtPool.stock_code == record.stock_code
                    )
                ).first() is not None
                
                # 查询是否龙虎榜
                is_lhb = db.query(LhbDetail).filter(
                    and_(
                        LhbDetail.date == record.date,
                        LhbDetail.stock_code == record.stock_code
                    )
                ).first() is not None
                
                # 更新标志（只在有变化时更新）
                if record.is_limit_up != is_limit_up:
                    record.is_limit_up = is_limit_up
                    updated_limit_up += 1
                
                if record.is_lhb != is_lhb:
                    record.is_lhb = is_lhb
                    updated_lhb += 1
                
                processed += 1
            
            # 提交当前批次
            db.commit()
            offset += batch_size
        
        return {
            "total_processed": processed,
            "updated_limit_up": updated_limit_up,
            "updated_lhb": updated_lhb
        }
    
    @staticmethod
    def get_fund_flow_list(
        db: Session,
        target_date: date,
        stock_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[StockFundFlow], int]:
        """获取资金流列表"""
        query = db.query(StockFundFlow).filter(StockFundFlow.date == target_date)
        
        if stock_code:
            query = query.filter(StockFundFlow.stock_code == stock_code)

        # 排序
        if sort_by:
            col = getattr(StockFundFlow, sort_by, None)
            if col is not None:
                if order == "asc":
                    query = query.order_by(col.asc())
                else:
                    query = query.order_by(col.desc())
        else:
            # 默认按主力净流入倒序
            query = query.order_by(StockFundFlow.main_net_inflow.desc())
        
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def get_fund_flow_history(
        db: Session,
        stock_code: str,
        start_date: date,
        end_date: date
    ) -> List[StockFundFlow]:
        """获取资金流历史"""
        return db.query(StockFundFlow).filter(
            and_(
                StockFundFlow.stock_code == stock_code,
                StockFundFlow.date >= start_date,
                StockFundFlow.date <= end_date
            )
        ).order_by(StockFundFlow.date).all()
    
    @staticmethod
    def save_fund_flow_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """保存资金流数据"""
        count = 0
        for _, row in df.iterrows():
            # 尝试多种可能的字段名（优先使用实际接口返回的字段名）
            stock_code = str(row.get("股票代码", row.get("代码", row.get("code", "")))).zfill(6)
            stock_name = row.get("股票简称", row.get("名称", row.get("name", "")))
            
            if not stock_code or not stock_name or stock_code == "000000":
                continue
            
            existing = db.query(StockFundFlow).filter(
                and_(
                    StockFundFlow.date == target_date,
                    StockFundFlow.stock_code == stock_code
                )
            ).first()
            
            # 获取所有字段（优先使用实际接口返回的字段名）
            # 接口返回字段: 股票代码, 股票简称, 最新价, 涨跌幅, 换手率, 流入资金, 流出资金, 净额, 成交额
            current_price = row.get("最新价", row.get("current_price", None))
            change_percent = row.get("涨跌幅", row.get("涨幅", row.get("change_percent", None)))
            turnover_rate = row.get("换手率", row.get("turnover_rate", None))
            main_inflow = row.get("流入资金", row.get("主力流入", row.get("main_inflow", None)))
            main_outflow = row.get("流出资金", row.get("主力流出", row.get("main_outflow", None)))
            main_net_inflow = row.get("净额", row.get("主力净流入", row.get("main_net_inflow", row.get("净流入", None))))
            turnover_amount = row.get("成交额", row.get("turnover_amount", None))
            
            # 处理带单位的数值（如 "11.71亿" -> 1171000000）
            def parse_amount(value):
                if value is None or value == "":
                    return None
                if isinstance(value, (int, float)):
                    return float(value)
                value_str = str(value).strip()
                if "亿" in value_str:
                    num = float(value_str.replace("亿", "").strip())
                    return int(num * 100000000)
                elif "万" in value_str:
                    num = float(value_str.replace("万", "").strip())
                    return int(num * 10000)
                else:
                    try:
                        return float(value_str)
                    except:
                        return None
            
            # 处理最新价（直接转换为浮点数）
            if current_price is not None:
                try:
                    if isinstance(current_price, str):
                        current_price = float(current_price.strip())
                    else:
                        current_price = float(current_price)
                except:
                    current_price = None
            
            # 处理涨幅（去除百分号）
            if change_percent is not None:
                if isinstance(change_percent, str):
                    change_percent = change_percent.replace("%", "").strip()
                try:
                    change_percent = float(change_percent)
                except:
                    change_percent = None
            
            # 处理换手率（去除百分号）
            if turnover_rate is not None:
                if isinstance(turnover_rate, str):
                    turnover_rate = turnover_rate.replace("%", "").strip()
                try:
                    turnover_rate = float(turnover_rate)
                except:
                    turnover_rate = None
            
            # 处理金额字段（流入资金、流出资金、净额、成交额）
            main_inflow = parse_amount(main_inflow)
            main_outflow = parse_amount(main_outflow)
            main_net_inflow = parse_amount(main_net_inflow)
            turnover_amount = parse_amount(turnover_amount)
            
            # 查询是否涨停
            is_limit_up = db.query(ZtPool).filter(
                and_(
                    ZtPool.date == target_date,
                    ZtPool.stock_code == stock_code
                )
            ).first() is not None
            
            # 查询是否龙虎榜
            is_lhb = db.query(LhbDetail).filter(
                and_(
                    LhbDetail.date == target_date,
                    LhbDetail.stock_code == stock_code
                )
            ).first() is not None
            
            if existing:
                existing.stock_name = stock_name
                if current_price is not None:
                    existing.current_price = current_price
                if change_percent is not None:
                    existing.change_percent = change_percent
                if turnover_rate is not None:
                    existing.turnover_rate = turnover_rate
                if main_inflow is not None:
                    existing.main_inflow = main_inflow
                if main_outflow is not None:
                    existing.main_outflow = main_outflow
                if main_net_inflow is not None:
                    existing.main_net_inflow = main_net_inflow
                if turnover_amount is not None:
                    existing.turnover_amount = turnover_amount
                existing.is_limit_up = is_limit_up
                existing.is_lhb = is_lhb
            else:
                fund_flow = StockFundFlow(
                    date=target_date,
                    stock_code=stock_code,
                    stock_name=stock_name,
                    current_price=current_price,
                    change_percent=change_percent,
                    turnover_rate=turnover_rate,
                    main_inflow=main_inflow,
                    main_outflow=main_outflow,
                    main_net_inflow=main_net_inflow,
                    turnover_amount=turnover_amount,
                    is_limit_up=is_limit_up,
                    is_lhb=is_lhb,
                )
                db.add(fund_flow)
            
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date):
        """
        同步资金流数据
        从AKShare获取数据并保存到数据库
        使用接口: stock_fund_flow_individual
        """
        from app.utils.sync_result import SyncResult
        
        try:
            # 使用 symbol="即时" 获取实时资金流数据
            df = safe_akshare_call(ak.stock_fund_flow_individual, symbol="即时")
            
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的资金流数据，接口返回空或网络异常"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")
            
            count = FundFlowService.save_fund_flow_data(db, target_date, df)
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的资金流数据，共 {count} 条")
            return SyncResult.success_result(f"资金流数据同步成功", count)
        except Exception as e:
            error_msg = f"同步资金流数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)

    @staticmethod
    def get_concept_fund_flow(limit: int = 50) -> list[dict]:
        """
        获取概念资金流（实时），使用 stock_fund_flow_concept
        返回前 limit 条（按净额降序）
        """
        df: pd.DataFrame = safe_akshare_call(ak.stock_fund_flow_concept, symbol="即时")
        if df is None or df.empty:
            return []
        df = df.rename(columns={
            "行业": "concept",
            "行业指数": "index_value",
            "行业-涨跌幅": "index_change_percent",
            "流入资金": "inflow",
            "流出资金": "outflow",
            "净额": "net_amount",
            "公司家数": "stock_count",
            "领涨股": "leader_stock",
            "领涨股-涨跌幅": "leader_change_percent",
            "当前价": "leader_price",
        })
        # 排序取前 limit
        df = df.sort_values(by="net_amount", ascending=False).head(limit)
        # 数值转 float，便于序列化
        numeric_cols = ["index_value", "index_change_percent", "inflow", "outflow", "net_amount",
                        "leader_change_percent", "leader_price"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.fillna("").to_dict(orient="records")

    @staticmethod
    def sync_concept_fund_flow(db: Session, target_date: date, limit: int = 200):
        """
        同步概念资金流（stock_fund_flow_concept, symbol='即时'）
        存储到 concept_fund_flow，按 date + concept 去重覆盖
        """
        from app.utils.sync_result import SyncResult
        
        try:
            df: pd.DataFrame = safe_akshare_call(ak.stock_fund_flow_concept, symbol="即时")
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的概念资金流数据，接口返回空或网络异常"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")

            df = df.rename(columns={
                "行业": "concept",
                "行业指数": "index_value",
                "行业-涨跌幅": "index_change_percent",
                "流入资金": "inflow",
                "流出资金": "outflow",
                "净额": "net_amount",
                "公司家数": "stock_count",
                "领涨股": "leader_stock",
                "领涨股-涨跌幅": "leader_change_percent",
                "当前价": "leader_price",
            })

            # 数值列转 float
            numeric_cols = ["index_value", "index_change_percent", "inflow", "outflow", "net_amount",
                            "stock_count", "leader_change_percent", "leader_price"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
            # 取前 limit 按净额排序
            df = df.sort_values(by="net_amount", ascending=False).head(limit)

            count = 0
            for _, row in df.iterrows():
                concept = str(row.get("concept") or "").strip()
                if not concept:
                    continue
                existing = db.query(ConceptFundFlow).filter(
                    and_(
                        ConceptFundFlow.date == target_date,
                        ConceptFundFlow.concept == concept
                    )
                ).first()
                data = {
                    "index_value": row.get("index_value"),
                    "index_change_percent": row.get("index_change_percent"),
                    "inflow": row.get("inflow"),
                    "outflow": row.get("outflow"),
                    "net_amount": row.get("net_amount"),
                    "stock_count": row.get("stock_count"),
                    "leader_stock": row.get("leader_stock"),
                    "leader_change_percent": row.get("leader_change_percent"),
                    "leader_price": row.get("leader_price"),
                }
                if existing:
                    for k, v in data.items():
                        setattr(existing, k, v)
                else:
                    rec = ConceptFundFlow(
                        date=target_date,
                        concept=concept,
                        **data,
                    )
                    db.add(rec)
                count += 1
            
            try:
                db.commit()
                if count == 0:
                    return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
                print(f"成功同步 {target_date} 的概念资金流数据，共 {count} 条")
                return SyncResult.success_result(f"概念资金流数据同步成功", count)
            except Exception as e:
                db.rollback()
                error_msg = f"保存概念资金流数据失败: {str(e)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                return SyncResult.failure_result(str(e), error_msg)
        except Exception as e:
            error_msg = f"同步概念资金流数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            db.rollback()
            return SyncResult.failure_result(str(e), error_msg)

    @staticmethod
    def get_concept_fund_flow_db(
        db: Session,
        target_date: date,
        limit: int = 200
    ) -> List[ConceptFundFlow]:
        """获取指定日期的概念资金流，按净额倒序"""
        q = db.query(ConceptFundFlow).filter(ConceptFundFlow.date == target_date)
        q = q.order_by(ConceptFundFlow.net_amount.desc())
        if limit:
            q = q.limit(limit)
        return q.all()

    @staticmethod
    def sync_industry_fund_flow(db: Session, target_date: date, limit: int = 200) -> bool:
        """
        同步行业资金流（stock_fund_flow_industry, symbol='即时'）
        存储到 industry_fund_flow，按 date + industry 去重覆盖
        """
        df: pd.DataFrame = safe_akshare_call(ak.stock_fund_flow_industry, symbol="即时")
        if df is None or df.empty:
            print(f"未获取到 {target_date} 的行业资金流数据")
            return False
        
        df = df.rename(columns={
            "行业": "industry",
            "行业指数": "index_value",
            "行业-涨跌幅": "index_change_percent",
            "流入资金": "inflow",
            "流出资金": "outflow",
            "净额": "net_amount",
            "公司家数": "stock_count",
            "领涨股": "leader_stock",
            "领涨股-涨跌幅": "leader_change_percent",
            "当前价": "leader_price",
        })
        # 数值列转 float
        numeric_cols = ["index_value", "index_change_percent", "inflow", "outflow", "net_amount",
                        "stock_count", "leader_change_percent", "leader_price"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # 取前 limit 按净额排序
        df = df.sort_values(by="net_amount", ascending=False).head(limit)
        
        count = 0
        for _, row in df.iterrows():
            industry = str(row.get("industry") or "").strip()
            if not industry:
                continue
            existing = db.query(IndustryFundFlow).filter(
                and_(
                    IndustryFundFlow.date == target_date,
                    IndustryFundFlow.industry == industry
                )
            ).first()
            data = {
                "index_value": row.get("index_value"),
                "index_change_percent": row.get("index_change_percent"),
                "inflow": row.get("inflow"),
                "outflow": row.get("outflow"),
                "net_amount": row.get("net_amount"),
                "stock_count": row.get("stock_count"),
                "leader_stock": row.get("leader_stock"),
                "leader_change_percent": row.get("leader_change_percent"),
                "leader_price": row.get("leader_price"),
            }
            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
            else:
                rec = IndustryFundFlow(
                    date=target_date,
                    industry=industry,
                    **data,
                )
                db.add(rec)
            count += 1
        db.commit()
        print(f"成功同步 {target_date} 的行业资金流数据，共 {count} 条")
        return count > 0

    @staticmethod
    def get_industry_fund_flow(
        db: Session,
        target_date: date,
        limit: int = 200
    ) -> List[IndustryFundFlow]:
        """获取指定日期的行业资金流，按净额倒序"""
        q = db.query(IndustryFundFlow).filter(IndustryFundFlow.date == target_date)
        q = q.order_by(IndustryFundFlow.net_amount.desc())
        if limit:
            q = q.limit(limit)
        return q.all()

