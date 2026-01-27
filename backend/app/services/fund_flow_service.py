"""
资金流服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from typing import Optional, List, Dict, Set, Tuple
from datetime import date
import pandas as pd
from sqlalchemy import Index

from app.models.fund_flow import StockFundFlow, IndustryFundFlow, ConceptFundFlow
from app.models.stock_concept import StockConceptMapping, StockConcept
from app.models.zt_pool import ZtPool
from app.models.lhb import LhbDetail
from app.utils.akshare_utils import safe_akshare_call
from app.schemas.fund_flow import (
    DateRangeCondition, NetInflowRange, LimitUpCountRange,
    ConceptDateRangeCondition, ConceptFundFlowFilterRequest
)
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
        性能优化：使用批量查询避免N+1问题
        
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
        
        # 批量预加载涨停和龙虎榜数据，避免N+1查询
        zt_pool_records = db.query(ZtPool.date, ZtPool.stock_code).filter(
            and_(
                ZtPool.date >= start_date,
                ZtPool.date <= end_date
            )
        ).all()
        zt_pool_set = {(r.date, r.stock_code) for r in zt_pool_records}
        
        lhb_records = db.query(LhbDetail.date, LhbDetail.stock_code).filter(
            and_(
                LhbDetail.date >= start_date,
                LhbDetail.date <= end_date
            )
        ).all()
        lhb_set = {(r.date, r.stock_code) for r in lhb_records}
        
        offset = 0
        while offset < total_count:
            records = query.offset(offset).limit(batch_size).all()
            
            if not records:
                break
            
            for record in records:
                # 使用预加载的集合快速查找
                is_limit_up = (record.date, record.stock_code) in zt_pool_set
                is_lhb = (record.date, record.stock_code) in lhb_set
                
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
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        consecutive_days: Optional[int] = None,
        min_net_inflow: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[StockFundFlow], int]:
        """
        获取资金流列表
        
        Args:
            consecutive_days: 连续N日，净流入>M的查询条件（N）
            min_net_inflow: 连续N日，净流入>M的查询条件（M，单位：元）
        """
        query = db.query(StockFundFlow).filter(StockFundFlow.date == target_date)
        
        if stock_code:
            query = query.filter(StockFundFlow.stock_code == stock_code)
        
        # 连续N日净流入>M的筛选
        if consecutive_days is not None and min_net_inflow is not None:
            from app.utils.date_utils import get_trading_dates_before
            
            # 获取从target_date往前推consecutive_days个交易日
            trading_dates = get_trading_dates_before(db, target_date, consecutive_days)
            
            if len(trading_dates) < consecutive_days:
                # 如果交易日不足，返回空结果
                query = query.filter(StockFundFlow.id == -1)
            else:
                # 查询在这N个交易日中，每天净流入都>M的股票
                # 对于每个股票，检查是否在这N天中每天都有数据且净流入>M
                
                # 先查询所有在这N天中有数据的股票
                all_stocks_query = db.query(
                    StockFundFlow.stock_code
                ).filter(
                    StockFundFlow.date.in_(trading_dates)
                ).distinct()
                
                all_stock_codes = {row[0] for row in all_stocks_query.all()}
                
                # 对于每个股票，检查是否在这N天中每天都有数据且净流入>M
                qualified_stock_codes = []
                for stock_code_candidate in all_stock_codes:
                    # 查询该股票在这N天的数据
                    stock_records = db.query(StockFundFlow).filter(
                        and_(
                            StockFundFlow.stock_code == stock_code_candidate,
                            StockFundFlow.date.in_(trading_dates)
                        )
                    ).all()
                    
                    # 构建日期到记录的映射
                    records_by_date = {r.date: r for r in stock_records}
                    
                    # 检查是否在这N天中每天都有数据且净流入>M
                    all_days_valid = True
                    for d in trading_dates:
                        if d not in records_by_date:
                            # 如果某一天没有数据，不满足条件
                            all_days_valid = False
                            break
                        
                        record = records_by_date[d]
                        # 检查净流入是否>M
                        if not record.main_net_inflow or record.main_net_inflow <= min_net_inflow:
                            all_days_valid = False
                            break
                    
                    if all_days_valid:
                        qualified_stock_codes.append(stock_code_candidate)
                
                if qualified_stock_codes:
                    query = query.filter(StockFundFlow.stock_code.in_(qualified_stock_codes))
                else:
                    # 如果没有满足条件的股票，返回空结果
                    query = query.filter(StockFundFlow.id == -1)
        
        # 概念板块筛选（通过关联表）
        if concept_ids or concept_names:
            concept_subquery = db.query(StockConceptMapping.stock_name).distinct()
            
            if concept_ids:
                concept_subquery = concept_subquery.filter(
                    StockConceptMapping.concept_id.in_(concept_ids)
                )
            
            if concept_names:
                concept_subquery = concept_subquery.join(
                    StockConcept,
                    StockConceptMapping.concept_id == StockConcept.id
                ).filter(
                    StockConcept.name.in_(concept_names)
                )
            
            stock_names = [row[0] for row in concept_subquery.all()]
            if stock_names:
                query = query.filter(StockFundFlow.stock_name.in_(stock_names))
            else:
                # 如果没有匹配的概念板块，返回空结果
                query = query.filter(StockFundFlow.id == -1)

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
        
        # 批量加载概念板块，避免N+1查询
        if items:
            from app.services.stock_concept_service import StockConceptService
            from app.models.stock_concept import StockConcept, StockConceptMapping
            
            # 获取所有股票名称
            stock_names = [item.stock_name for item in items]
            
            # 批量查询所有股票的概念映射
            concept_mappings = db.query(
                StockConceptMapping.stock_name,
                StockConcept
            ).join(
                StockConcept,
                StockConceptMapping.concept_id == StockConcept.id
            ).filter(
                StockConceptMapping.stock_name.in_(stock_names)
            ).order_by(
                StockConcept.level.asc(),
                StockConcept.sort_order.asc(),
                StockConcept.name.asc()
            ).all()
            
            # 按股票名称分组概念
            concepts_by_stock = {}
            for stock_name, concept in concept_mappings:
                if stock_name not in concepts_by_stock:
                    concepts_by_stock[stock_name] = []
                concepts_by_stock[stock_name].append(concept)
            
            # 为每个记录设置概念板块
            for item in items:
                concepts = concepts_by_stock.get(item.stock_name, [])
                setattr(item, '_concepts', concepts)
        
        return items, total
    
    @staticmethod
    def get_fund_flow_list_by_date_range(
        db: Session,
        start_date: date,
        end_date: date,
        stock_code: Optional[str] = None,
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        consecutive_days: Optional[int] = None,
        min_net_inflow: Optional[float] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[StockFundFlow], int]:
        """
        获取日期范围内的资金流列表（按股票代码聚合）
        
        对于多日查询，会按股票代码分组并聚合数据：
        - 流入、流出、净流入、成交额：汇总多日数据
        - 最新价、涨幅、换手率：使用最新日期的值
        - 涨停、龙虎榜：如果任意一天有，则为True
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            consecutive_days: 连续N日，净流入>M的查询条件（N）
            min_net_inflow: 连续N日，净流入>M的查询条件（M，单位：元）
        """
        # 基础查询：日期范围内的所有数据
        query = db.query(StockFundFlow).filter(
            and_(
                StockFundFlow.date >= start_date,
                StockFundFlow.date <= end_date
            )
        )
        
        if stock_code:
            query = query.filter(StockFundFlow.stock_code == stock_code)
        
        # 连续N日净流入>M的筛选
        if consecutive_days is not None and min_net_inflow is not None:
            from app.utils.date_utils import get_trading_dates_before
            
            # 获取从end_date往前推consecutive_days个交易日
            trading_dates = get_trading_dates_before(db, end_date, consecutive_days)
            
            if len(trading_dates) < consecutive_days:
                # 如果交易日不足，返回空结果
                query = query.filter(StockFundFlow.id == -1)
            else:
                # 查询在这N个交易日中，每天净流入都>M的股票
                all_stocks_query = db.query(
                    StockFundFlow.stock_code
                ).filter(
                    StockFundFlow.date.in_(trading_dates)
                ).distinct()
                
                all_stock_codes = {row[0] for row in all_stocks_query.all()}
                
                qualified_stock_codes = []
                for stock_code_candidate in all_stock_codes:
                    stock_records = db.query(StockFundFlow).filter(
                        and_(
                            StockFundFlow.stock_code == stock_code_candidate,
                            StockFundFlow.date.in_(trading_dates)
                        )
                    ).all()
                    
                    records_by_date = {r.date: r for r in stock_records}
                    
                    all_days_valid = True
                    for d in trading_dates:
                        if d not in records_by_date:
                            all_days_valid = False
                            break
                        
                        record = records_by_date[d]
                        if not record.main_net_inflow or record.main_net_inflow <= min_net_inflow:
                            all_days_valid = False
                            break
                    
                    if all_days_valid:
                        qualified_stock_codes.append(stock_code_candidate)
                
                if qualified_stock_codes:
                    query = query.filter(StockFundFlow.stock_code.in_(qualified_stock_codes))
                else:
                    query = query.filter(StockFundFlow.id == -1)
        
        # 概念板块筛选
        if concept_ids or concept_names:
            concept_subquery = db.query(StockConceptMapping.stock_name).distinct()
            
            if concept_ids:
                concept_subquery = concept_subquery.filter(
                    StockConceptMapping.concept_id.in_(concept_ids)
                )
            
            if concept_names:
                concept_subquery = concept_subquery.join(
                    StockConcept,
                    StockConceptMapping.concept_id == StockConcept.id
                ).filter(
                    StockConcept.name.in_(concept_names)
                )
            
            stock_names = [row[0] for row in concept_subquery.all()]
            if stock_names:
                query = query.filter(StockFundFlow.stock_name.in_(stock_names))
            else:
                query = query.filter(StockFundFlow.id == -1)
        
        # 获取所有原始数据
        all_records = query.order_by(
            StockFundFlow.stock_code.asc(),
            StockFundFlow.date.desc()
        ).all()
        
        # 按股票代码分组并聚合
        aggregated_data = {}
        for record in all_records:
            code = record.stock_code
            if code not in aggregated_data:
                # 初始化聚合数据（使用最新日期的记录作为基础）
                aggregated_data[code] = {
                    'stock_code': code,
                    'stock_name': record.stock_name,
                    'date': record.date,  # 最新日期
                    'current_price': record.current_price,
                    'change_percent': record.change_percent,
                    'turnover_rate': record.turnover_rate,
                    'main_inflow': record.main_inflow or 0,
                    'main_outflow': record.main_outflow or 0,
                    'main_net_inflow': record.main_net_inflow or 0,
                    'turnover_amount': record.turnover_amount or 0,
                    'is_limit_up': record.is_limit_up or False,
                    'is_lhb': record.is_lhb or False,
                }
            else:
                # 累计金额字段
                aggregated_data[code]['main_inflow'] += (record.main_inflow or 0)
                aggregated_data[code]['main_outflow'] += (record.main_outflow or 0)
                aggregated_data[code]['main_net_inflow'] += (record.main_net_inflow or 0)
                aggregated_data[code]['turnover_amount'] += (record.turnover_amount or 0)
                # 涨停和龙虎榜：任意一天有则为True
                if record.is_limit_up:
                    aggregated_data[code]['is_limit_up'] = True
                if record.is_lhb:
                    aggregated_data[code]['is_lhb'] = True
        
        # 转换为StockFundFlow对象列表
        aggregated_items = []
        for code, data in aggregated_data.items():
            # 创建一个类似StockFundFlow的对象
            # 由于我们需要返回StockFundFlow对象，我们创建一个临时对象
            item = StockFundFlow(
                date=data['date'],
                stock_code=data['stock_code'],
                stock_name=data['stock_name'],
                current_price=data['current_price'],
                change_percent=data['change_percent'],
                turnover_rate=data['turnover_rate'],
                main_inflow=data['main_inflow'],
                main_outflow=data['main_outflow'],
                main_net_inflow=data['main_net_inflow'],
                turnover_amount=data['turnover_amount'],
                is_limit_up=data['is_limit_up'],
                is_lhb=data['is_lhb'],
            )
            aggregated_items.append(item)
        
        # 排序
        if sort_by:
            col = getattr(StockFundFlow, sort_by, None)
            if col is not None:
                if order == "asc":
                    aggregated_items.sort(key=lambda x: getattr(x, sort_by) or 0)
                else:
                    aggregated_items.sort(key=lambda x: getattr(x, sort_by) or 0, reverse=True)
        else:
            # 默认按主力净流入倒序
            aggregated_items.sort(key=lambda x: x.main_net_inflow or 0, reverse=True)
        
        total = len(aggregated_items)
        
        # 分页
        offset = (page - 1) * page_size
        paginated_items = aggregated_items[offset:offset + page_size]
        
        # 批量加载概念板块
        if paginated_items:
            stock_names = [item.stock_name for item in paginated_items]
            
            concept_mappings = db.query(
                StockConceptMapping.stock_name,
                StockConcept
            ).join(
                StockConcept,
                StockConceptMapping.concept_id == StockConcept.id
            ).filter(
                StockConceptMapping.stock_name.in_(stock_names)
            ).order_by(
                StockConcept.level.asc(),
                StockConcept.sort_order.asc(),
                StockConcept.name.asc()
            ).all()
            
            concepts_by_stock = {}
            for stock_name, concept in concept_mappings:
                if stock_name not in concepts_by_stock:
                    concepts_by_stock[stock_name] = []
                concepts_by_stock[stock_name].append(concept)
            
            for item in paginated_items:
                concepts = concepts_by_stock.get(item.stock_name, [])
                setattr(item, '_concepts', concepts)
        
        return paginated_items, total
    
    @staticmethod
    def get_concepts_for_fund_flow(db: Session, fund_flow: StockFundFlow) -> List:
        """获取资金流记录的概念板块列表（包含层级信息）"""
        from app.services.stock_concept_service import StockConceptService
        return StockConceptService.get_stock_concepts_with_hierarchy(db, fund_flow.stock_name)
    
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
        """
        保存资金流数据
        性能优化：批量预加载涨停和龙虎榜数据，避免N+1查询
        """
        # 批量预加载涨停和龙虎榜数据，避免N+1查询
        zt_pool_codes = db.query(ZtPool.stock_code).filter(
            ZtPool.date == target_date
        ).distinct().all()
        zt_pool_set = {r[0] for r in zt_pool_codes}
        
        lhb_codes = db.query(LhbDetail.stock_code).filter(
            LhbDetail.date == target_date
        ).distinct().all()
        lhb_set = {r[0] for r in lhb_codes}
        
        # 批量查询已存在的记录
        stock_codes = []
        for _, row in df.iterrows():
            stock_code = str(row.get("股票代码", row.get("代码", row.get("code", "")))).zfill(6)
            if stock_code and stock_code != "000000":
                stock_codes.append(stock_code)
        
        existing_records = {}
        if stock_codes:
            existing_list = db.query(StockFundFlow).filter(
                and_(
                    StockFundFlow.date == target_date,
                    StockFundFlow.stock_code.in_(stock_codes)
                )
            ).all()
            existing_records = {(r.date, r.stock_code): r for r in existing_list}
        
        count = 0
        for _, row in df.iterrows():
            # 尝试多种可能的字段名（优先使用实际接口返回的字段名）
            stock_code = str(row.get("股票代码", row.get("代码", row.get("code", "")))).zfill(6)
            stock_name = row.get("股票简称", row.get("名称", row.get("name", "")))
            
            if not stock_code or not stock_name or stock_code == "000000":
                continue
            
            existing = existing_records.get((target_date, stock_code))
            
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
            
            # 使用预加载的集合快速查找
            is_limit_up = stock_code in zt_pool_set
            is_lhb = stock_code in lhb_set
            
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
    def get_concept_fund_flow_by_date_range(
        db: Session,
        start_date: date,
        end_date: date,
        concepts: Optional[List[str]] = None,
        min_net_amount: Optional[float] = None,
        max_net_amount: Optional[float] = None,
        min_inflow: Optional[float] = None,
        max_inflow: Optional[float] = None,
        min_outflow: Optional[float] = None,
        max_outflow: Optional[float] = None,
        min_index_change_percent: Optional[float] = None,
        max_index_change_percent: Optional[float] = None,
        min_stock_count: Optional[int] = None,
        max_stock_count: Optional[int] = None,
        sort_by: Optional[str] = "net_amount",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ConceptFundFlow], int]:
        """
        跨日期查询概念资金流，支持多条件联合查询
        
        Args:
            db: 数据库会话
            start_date: 开始日期
            end_date: 结束日期
            concepts: 概念名称列表（支持模糊匹配）
            min_net_amount: 最小净额
            max_net_amount: 最大净额
            min_inflow: 最小流入资金
            max_inflow: 最大流入资金
            min_outflow: 最小流出资金
            max_outflow: 最大流出资金
            min_index_change_percent: 最小指数涨跌幅
            max_index_change_percent: 最大指数涨跌幅
            min_stock_count: 最小公司家数
            max_stock_count: 最大公司家数
            sort_by: 排序字段
            order: 排序方向
            page: 页码
            page_size: 每页数量
            
        Returns:
            Tuple[List[ConceptFundFlow], int]: (查询结果列表, 总记录数)
        """
        # 构建基础查询
        q = db.query(ConceptFundFlow).filter(
            and_(
                ConceptFundFlow.date >= start_date,
                ConceptFundFlow.date <= end_date
            )
        )
        
        # 概念名称筛选（支持模糊匹配）
        if concepts:
            concept_filters = []
            for concept in concepts:
                concept_filters.append(ConceptFundFlow.concept.like(f"%{concept}%"))
            q = q.filter(or_(*concept_filters))
        
        # 净额筛选
        if min_net_amount is not None:
            q = q.filter(ConceptFundFlow.net_amount >= min_net_amount)
        if max_net_amount is not None:
            q = q.filter(ConceptFundFlow.net_amount <= max_net_amount)
        
        # 流入资金筛选
        if min_inflow is not None:
            q = q.filter(ConceptFundFlow.inflow >= min_inflow)
        if max_inflow is not None:
            q = q.filter(ConceptFundFlow.inflow <= max_inflow)
        
        # 流出资金筛选
        if min_outflow is not None:
            q = q.filter(ConceptFundFlow.outflow >= min_outflow)
        if max_outflow is not None:
            q = q.filter(ConceptFundFlow.outflow <= max_outflow)
        
        # 指数涨跌幅筛选
        if min_index_change_percent is not None:
            q = q.filter(ConceptFundFlow.index_change_percent >= min_index_change_percent)
        if max_index_change_percent is not None:
            q = q.filter(ConceptFundFlow.index_change_percent <= max_index_change_percent)
        
        # 公司家数筛选
        if min_stock_count is not None:
            q = q.filter(ConceptFundFlow.stock_count >= min_stock_count)
        if max_stock_count is not None:
            q = q.filter(ConceptFundFlow.stock_count <= max_stock_count)
        
        # 排序
        sort_column_map = {
            "net_amount": ConceptFundFlow.net_amount,
            "inflow": ConceptFundFlow.inflow,
            "outflow": ConceptFundFlow.outflow,
            "index_change_percent": ConceptFundFlow.index_change_percent,
            "date": ConceptFundFlow.date,
            "stock_count": ConceptFundFlow.stock_count,
        }
        
        sort_column = sort_column_map.get(sort_by, ConceptFundFlow.net_amount)
        if order.lower() == "asc":
            q = q.order_by(asc(sort_column))
        else:
            q = q.order_by(desc(sort_column))
        
        # 先获取总数（在排序和分页之前）
        # 使用子查询优化，避免对大量数据进行排序后再计数
        total = q.count()
        
        # 分页
        offset = (page - 1) * page_size
        q = q.offset(offset).limit(page_size)
        
        return q.all(), total

    @staticmethod
    def filter_concept_fund_flow_by_conditions(
        db: Session,
        conditions: List[ConceptDateRangeCondition],
        concepts: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = "net_amount",
        order: str = "desc"
    ) -> Tuple[List[Dict], int]:
        """
        多条件联合查询概念资金流
        
        多个条件之间是AND关系，即概念必须同时满足所有条件
        
        Args:
            db: 数据库会话
            conditions: 筛选条件列表
            concepts: 概念名称列表（可选，支持模糊匹配）
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序方向
            
        Returns:
            Tuple[List[Dict], int]: (查询结果列表, 总记录数)
        """
        if not conditions:
            return [], 0
        
        # 收集所有需要查询的概念
        concept_set: Set[str] = set()
        
        # 对每个条件，查询满足条件的概念
        for condition in conditions:
            date_range = condition.date_range
            
            # 构建该条件的查询
            q = db.query(ConceptFundFlow.concept)
            
            # 如果提供了日期范围，则添加日期过滤条件
            if date_range and date_range.start and date_range.end:
                q = q.filter(
                    and_(
                        ConceptFundFlow.date >= date_range.start,
                        ConceptFundFlow.date <= date_range.end
                    )
                )
            
            # 应用该条件的筛选
            if condition.net_amount:
                if condition.net_amount.min is not None:
                    q = q.filter(ConceptFundFlow.net_amount >= condition.net_amount.min)
                if condition.net_amount.max is not None:
                    q = q.filter(ConceptFundFlow.net_amount <= condition.net_amount.max)
            
            if condition.inflow:
                if condition.inflow.min is not None:
                    q = q.filter(ConceptFundFlow.inflow >= condition.inflow.min)
                if condition.inflow.max is not None:
                    q = q.filter(ConceptFundFlow.inflow <= condition.inflow.max)
            
            if condition.outflow:
                if condition.outflow.min is not None:
                    q = q.filter(ConceptFundFlow.outflow >= condition.outflow.min)
                if condition.outflow.max is not None:
                    q = q.filter(ConceptFundFlow.outflow <= condition.outflow.max)
            
            if condition.index_change_percent:
                if condition.index_change_percent.min is not None:
                    q = q.filter(ConceptFundFlow.index_change_percent >= condition.index_change_percent.min)
                if condition.index_change_percent.max is not None:
                    q = q.filter(ConceptFundFlow.index_change_percent <= condition.index_change_percent.max)
            
            if condition.stock_count:
                if condition.stock_count.min is not None:
                    q = q.filter(ConceptFundFlow.stock_count >= condition.stock_count.min)
                if condition.stock_count.max is not None:
                    q = q.filter(ConceptFundFlow.stock_count <= condition.stock_count.max)
            
            # 获取满足该条件的概念集合
            condition_concepts = {row[0] for row in q.distinct().all()}
            
            # 第一个条件：直接使用
            if not concept_set:
                concept_set = condition_concepts
            else:
                # 后续条件：取交集（AND关系）
                concept_set = concept_set & condition_concepts
        
        # 如果没有满足所有条件的概念，返回空结果
        if not concept_set:
            return [], 0
        
        # 如果有额外的概念名称筛选，进一步过滤
        if concepts:
            filtered_concept_set = set()
            for c in concept_set:
                # 检查概念名称是否匹配任何一个筛选条件（模糊匹配）
                if any(concept.lower() in c.lower() for concept in concepts):
                    filtered_concept_set.add(c)
            concept_set = filtered_concept_set
        
        if not concept_set:
            return [], 0
        
        # 查询这些概念的所有数据
        # 如果所有条件都有日期范围，则在日期范围内查询；否则查询所有日期
        all_start_dates = [cond.date_range.start for cond in conditions if cond.date_range and cond.date_range.start]
        all_end_dates = [cond.date_range.end for cond in conditions if cond.date_range and cond.date_range.end]
        
        q = db.query(ConceptFundFlow).filter(
            ConceptFundFlow.concept.in_(list(concept_set))
        )
        
        # 如果存在日期范围，则添加日期过滤
        if all_start_dates and all_end_dates:
            min_start_date = min(all_start_dates)
            max_end_date = max(all_end_dates)
            q = q.filter(
                and_(
                    ConceptFundFlow.date >= min_start_date,
                    ConceptFundFlow.date <= max_end_date
                )
            )
        
        # 获取总数
        total = q.count()
        
        # 排序
        sort_column_map = {
            "net_amount": ConceptFundFlow.net_amount,
            "inflow": ConceptFundFlow.inflow,
            "outflow": ConceptFundFlow.outflow,
            "index_change_percent": ConceptFundFlow.index_change_percent,
            "date": ConceptFundFlow.date,
            "stock_count": ConceptFundFlow.stock_count,
        }
        
        sort_column = sort_column_map.get(sort_by, ConceptFundFlow.net_amount)
        if order.lower() == "asc":
            q = q.order_by(asc(sort_column))
        else:
            q = q.order_by(desc(sort_column))
        
        # 分页
        offset = (page - 1) * page_size
        q = q.offset(offset).limit(page_size)
        
        # 转换为字典列表，添加匹配条件信息
        results = []
        for item in q.all():
            item_dict = {
                column.name: getattr(item, column.name)
                for column in item.__table__.columns
            }
            # 添加匹配的条件信息
            match_conditions = []
            for idx, condition in enumerate(conditions):
                # 检查该记录是否满足该条件
                # 如果条件有日期范围，则检查日期是否在范围内；否则只检查概念是否匹配
                date_match = True
                if condition.date_range and condition.date_range.start and condition.date_range.end:
                    date_match = condition.date_range.start <= item.date <= condition.date_range.end
                
                if date_match and item.concept in concept_set:
                    match_condition = {
                        "condition_index": idx,
                        "date": item.date.isoformat()
                    }
                    if condition.date_range and condition.date_range.start and condition.date_range.end:
                        match_condition["date_range"] = {
                            "start": condition.date_range.start.isoformat(),
                            "end": condition.date_range.end.isoformat()
                        }
                    match_conditions.append(match_condition)
            item_dict["match_conditions"] = match_conditions
            results.append(item_dict)
        
        return results, total

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
    
    @staticmethod
    def filter_fund_flow_by_conditions(
        db: Session,
        conditions: List[DateRangeCondition],
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[Dict], int]:
        """
        根据多个日期范围条件筛选资金流数据
        
        Args:
            db: 数据库会话
            conditions: 筛选条件列表，每个条件包含日期范围和主力净流入区间
            concept_ids: 概念板块ID列表（可选）
            concept_names: 概念板块名称列表（可选）
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            order: 排序方向
        
        Returns:
            tuple: (结果列表, 总数)
        """
        if not conditions:
            return [], 0
        
        # 第一步：对每个条件，找到满足条件的股票代码集合
        matched_stock_sets: List[Set[str]] = []
        condition_details: List[Dict] = []
        
        for condition_idx, condition in enumerate(conditions):
            date_range = condition.date_range
            net_inflow_range = condition.main_net_inflow
            limit_up_count_range = condition.limit_up_count
            
            # 构建查询
            query = db.query(StockFundFlow.stock_code).filter(
                and_(
                    StockFundFlow.date >= date_range.start,
                    StockFundFlow.date <= date_range.end
                )
            )
            
            # 添加主力净流入条件
            if net_inflow_range:
                if net_inflow_range.min is not None:
                    query = query.filter(StockFundFlow.main_net_inflow >= net_inflow_range.min)
                if net_inflow_range.max is not None:
                    query = query.filter(StockFundFlow.main_net_inflow <= net_inflow_range.max)
            
            # 获取满足资金流条件的股票代码集合
            matched_stocks = set([row[0] for row in query.distinct().all()])
            
            # 如果有涨停次数限制，进一步筛选
            if limit_up_count_range and matched_stocks:
                # 统计每个股票在日期范围内的涨停次数
                limit_up_counts = {}
                for stock_code in matched_stocks:
                    count = db.query(func.count(ZtPool.id)).filter(
                        and_(
                            ZtPool.stock_code == stock_code,
                            ZtPool.date >= date_range.start,
                            ZtPool.date <= date_range.end
                        )
                    ).scalar() or 0
                    limit_up_counts[stock_code] = count
                
                # 根据涨停次数范围过滤
                filtered_stocks = set()
                for stock_code, count in limit_up_counts.items():
                    if limit_up_count_range.min is not None and count < limit_up_count_range.min:
                        continue
                    if limit_up_count_range.max is not None and count > limit_up_count_range.max:
                        continue
                    filtered_stocks.add(stock_code)
                
                matched_stocks = filtered_stocks
            
            matched_stock_sets.append(matched_stocks)
            
            # 记录条件详情
            condition_details.append({
                "condition_index": condition_idx,
                "date_range": {
                    "start": date_range.start.isoformat(),
                    "end": date_range.end.isoformat()
                },
                "main_net_inflow": {
                    "min": net_inflow_range.min if net_inflow_range else None,
                    "max": net_inflow_range.max if net_inflow_range else None
                } if net_inflow_range else None,
                "limit_up_count": {
                    "min": limit_up_count_range.min if limit_up_count_range else None,
                    "max": limit_up_count_range.max if limit_up_count_range else None
                } if limit_up_count_range else None,
                "matched_count": len(matched_stocks)
            })
        
        # 第二步：取所有条件的交集（AND关系）
        if not matched_stock_sets:
            return [], 0
        
        final_stock_codes = matched_stock_sets[0]
        for stock_set in matched_stock_sets[1:]:
            final_stock_codes = final_stock_codes.intersection(stock_set)
        
        if not final_stock_codes:
            return [], 0
        
        # 第三步：概念板块筛选（如果指定）
        if concept_ids or concept_names:
            concept_subquery = db.query(StockConceptMapping.stock_name).distinct()
            
            if concept_ids:
                concept_subquery = concept_subquery.filter(
                    StockConceptMapping.concept_id.in_(concept_ids)
                )
            
            if concept_names:
                concept_subquery = concept_subquery.join(
                    StockConcept,
                    StockConceptMapping.concept_id == StockConcept.id
                ).filter(
                    StockConcept.name.in_(concept_names)
                )
            
            concept_stock_names = set([row[0] for row in concept_subquery.all()])
            
            # 获取概念板块对应的股票代码
            if concept_stock_names:
                concept_stock_codes = db.query(StockFundFlow.stock_code).filter(
                    StockFundFlow.stock_name.in_(concept_stock_names)
                ).distinct().all()
                concept_stock_codes_set = set([row[0] for row in concept_stock_codes])
                final_stock_codes = final_stock_codes.intersection(concept_stock_codes_set)
            else:
                # 如果没有匹配的概念板块，返回空结果
                return [], 0
        
        # 第四步：获取每个股票的详细信息（使用最新日期）
        # 先获取每个股票的最新日期和对应的主力净流入
        stock_info_query = db.query(
            StockFundFlow.stock_code,
            StockFundFlow.stock_name,
            func.max(StockFundFlow.date).label('latest_date'),
            func.sum(StockFundFlow.main_net_inflow).label('total_net_inflow')
        ).filter(
            StockFundFlow.stock_code.in_(list(final_stock_codes))
        ).group_by(
            StockFundFlow.stock_code,
            StockFundFlow.stock_name
        )
        
        # 排序
        if sort_by == "main_net_inflow":
            if order == "asc":
                stock_info_query = stock_info_query.order_by(func.sum(StockFundFlow.main_net_inflow).asc())
            else:
                stock_info_query = stock_info_query.order_by(func.sum(StockFundFlow.main_net_inflow).desc())
        elif sort_by == "stock_code":
            if order == "asc":
                stock_info_query = stock_info_query.order_by(StockFundFlow.stock_code.asc())
            else:
                stock_info_query = stock_info_query.order_by(StockFundFlow.stock_code.desc())
        elif sort_by == "stock_name":
            if order == "asc":
                stock_info_query = stock_info_query.order_by(StockFundFlow.stock_name.asc())
            else:
                stock_info_query = stock_info_query.order_by(StockFundFlow.stock_name.desc())
        else:
            # 默认按主力净流入倒序
            stock_info_query = stock_info_query.order_by(func.sum(StockFundFlow.main_net_inflow).desc())
        
        # 获取总数
        total = stock_info_query.count()
        
        # 分页
        offset = (page - 1) * page_size
        stock_infos = stock_info_query.offset(offset).limit(page_size).all()
        
        # 第五步：构建结果（性能优化：批量查询避免N+1）
        results = []
        from app.services.stock_concept_service import StockConceptService
        from app.models.stock_concept import StockConcept, StockConceptMapping
        
        # 批量获取所有股票的最新记录
        stock_code_date_pairs = [(stock_code, latest_date) for stock_code, stock_name, latest_date, total_net_inflow in stock_infos]
        latest_records_map = {}
        if stock_code_date_pairs:
            # 构建查询条件：使用IN查询优化性能
            stock_codes_set = {stock_code for stock_code, _ in stock_code_date_pairs}
            dates_set = {date for _, date in stock_code_date_pairs}
            
            latest_records = db.query(StockFundFlow).filter(
                and_(
                    StockFundFlow.stock_code.in_(list(stock_codes_set)),
                    StockFundFlow.date.in_(list(dates_set))
                )
            ).all()
            
            # 按 (stock_code, date) 构建映射
            for r in latest_records:
                key = (r.stock_code, r.date)
                if key in stock_code_date_pairs:
                    latest_records_map[key] = r
        
        # 批量获取所有股票的概念板块
        stock_names = [stock_name for stock_code, stock_name, latest_date, total_net_inflow in stock_infos]
        concept_mappings = db.query(
            StockConceptMapping.stock_name,
            StockConcept
        ).join(
            StockConcept,
            StockConceptMapping.concept_id == StockConcept.id
        ).filter(
            StockConceptMapping.stock_name.in_(stock_names)
        ).order_by(
            StockConcept.level.asc(),
            StockConcept.sort_order.asc(),
            StockConcept.name.asc()
        ).all()
        
        concepts_by_stock = {}
        for stock_name, concept in concept_mappings:
            if stock_name not in concepts_by_stock:
                concepts_by_stock[stock_name] = []
            concepts_by_stock[stock_name].append(concept)
        
        # 批量获取所有日期范围内的资金流数据（用于匹配条件）
        all_date_ranges = [(cond.date_range.start, cond.date_range.end) for cond in conditions]
        min_start_date = min([dr[0] for dr in all_date_ranges])
        max_end_date = max([dr[1] for dr in all_date_ranges])
        
        stock_codes_list = [stock_code for stock_code, stock_name, latest_date, total_net_inflow in stock_infos]
        all_fund_flows = db.query(StockFundFlow).filter(
            and_(
                StockFundFlow.stock_code.in_(stock_codes_list),
                StockFundFlow.date >= min_start_date,
                StockFundFlow.date <= max_end_date
            )
        ).all()
        
        # 按股票代码和日期组织资金流数据
        fund_flows_by_stock_date = {}
        for ff in all_fund_flows:
            key = (ff.stock_code, ff.date)
            if key not in fund_flows_by_stock_date:
                fund_flows_by_stock_date[key] = []
            fund_flows_by_stock_date[key].append(ff)
        
        # 批量获取涨停数据
        zt_pool_records = db.query(ZtPool.stock_code, ZtPool.date).filter(
            and_(
                ZtPool.stock_code.in_(stock_codes_list),
                ZtPool.date >= min_start_date,
                ZtPool.date <= max_end_date
            )
        ).all()
        
        zt_pool_by_stock_date = {}
        for stock_code, zt_date in zt_pool_records:
            key = (stock_code, zt_date)
            if key not in zt_pool_by_stock_date:
                zt_pool_by_stock_date[key] = []
            zt_pool_by_stock_date[key].append(zt_date)
        
        for stock_code, stock_name, latest_date, total_net_inflow in stock_infos:
            # 获取最新日期的详细数据
            latest_record = latest_records_map.get((stock_code, latest_date))
            
            # 获取概念板块
            concepts = concepts_by_stock.get(stock_name, [])
            
            # 构建匹配条件详情（标记哪些条件被满足）
            match_conditions = []
            for cond_detail in condition_details:
                # 检查该股票是否满足此条件
                cond = conditions[cond_detail["condition_index"]]
                date_range = cond.date_range
                net_inflow_range = cond.main_net_inflow
                limit_up_count_range = cond.limit_up_count
                
                # 从预加载的数据中筛选匹配的记录
                matched_records = []
                for date_key in fund_flows_by_stock_date.keys():
                    if date_key[0] == stock_code and date_range.start <= date_key[1] <= date_range.end:
                        for ff in fund_flows_by_stock_date[date_key]:
                            if net_inflow_range:
                                if net_inflow_range.min is not None and (ff.main_net_inflow is None or ff.main_net_inflow < net_inflow_range.min):
                                    continue
                                if net_inflow_range.max is not None and (ff.main_net_inflow is None or ff.main_net_inflow > net_inflow_range.max):
                                    continue
                            matched_records.append(ff)
                
                # 查询涨停次数（从预加载的数据中）
                limit_up_count = None
                limit_up_dates = []
                if limit_up_count_range:
                    limit_up_dates_list = []
                    for date_key in zt_pool_by_stock_date.keys():
                        if date_key[0] == stock_code and date_range.start <= date_key[1] <= date_range.end:
                            limit_up_dates_list.append(date_key[1])
                    limit_up_count = len(limit_up_dates_list)
                    limit_up_dates = [d.isoformat() for d in limit_up_dates_list]
                
                match_conditions.append({
                    **cond_detail,
                    "matched_records": [
                        {
                            "date": rec.date.isoformat(),
                            "main_net_inflow": float(rec.main_net_inflow) if rec.main_net_inflow else None
                        }
                        for rec in matched_records
                    ],
                    "limit_up_count": limit_up_count,
                    "limit_up_dates": limit_up_dates
                })
            
            result = {
                "stock_code": stock_code,
                "stock_name": stock_name,
                "match_conditions": match_conditions,
                "latest_date": latest_date.isoformat() if latest_date else None,
                "latest_main_net_inflow": float(latest_record.main_net_inflow) if latest_record and latest_record.main_net_inflow else None,
                "concepts": [
                    {"id": c.id, "name": c.name, "code": c.code}
                    for c in concepts
                ] if concepts else []
            }
            results.append(result)
        
        return results, total

