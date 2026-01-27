"""
涨停池服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from typing import Optional, List, Dict
from datetime import date
import pandas as pd

from app.models.zt_pool import ZtPool, ZtPoolDown
from app.models.lhb import LhbDetail
from app.models.stock_concept import StockConceptMapping, StockConcept
from app.services.stock_concept_service import StockConceptService
from app.utils.akshare_utils import safe_akshare_call
from app.utils.format_utils import safe_float, safe_int
import akshare as ak


class ZtPoolService:
    """涨停池服务类"""
    
    @staticmethod
    def get_zt_pool_list(
        db: Session,
        start_date: date,
        end_date: date,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        concept: Optional[str] = None,
        industry: Optional[str] = None,
        consecutive_limit_count: Optional[int] = None,
        limit_up_statistics: Optional[str] = None,
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        is_lhb: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[ZtPool], int]:
        """
        获取涨停池列表
        
        Args:
            start_date: 开始日期（日期范围查询）
            end_date: 结束日期（日期范围查询）
            stock_name: 股票名称（模糊匹配）
            is_lhb: 是否龙虎榜筛选，True表示只返回龙虎榜股票，False表示只返回非龙虎榜股票，None表示不筛选
        """
        # 使用日期范围查询
        query = db.query(ZtPool).filter(
            ZtPool.date >= start_date,
            ZtPool.date <= end_date
        )
        
        if stock_code:
            query = query.filter(ZtPool.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            query = query.filter(ZtPool.stock_name.like(f"%{stock_name.strip()}%"))
        
        # 兼容旧的概念筛选（文本字段）
        if concept:
            query = query.filter(ZtPool.concept.like(f"%{concept}%"))
        
        if industry:
            query = query.filter(ZtPool.industry == industry)
        
        if consecutive_limit_count is not None:
            query = query.filter(ZtPool.consecutive_limit_count == consecutive_limit_count)
        
        # 板数筛选
        if limit_up_statistics:
            limit_up_statistics_trimmed = limit_up_statistics.strip()
            # 如果输入是"首板"，筛选"1/1"
            if limit_up_statistics_trimmed == "首板":
                query = query.filter(ZtPool.limit_up_statistics == "1/1")
            # 如果输入是纯数字（如"2"），筛选板数为该数字的记录（格式：*/2）
            elif limit_up_statistics_trimmed.isdigit():
                board_count = limit_up_statistics_trimmed
                query = query.filter(ZtPool.limit_up_statistics.like(f"%/{board_count}"))
            # 如果输入是完整格式（如"2/3"），精确匹配
            elif "/" in limit_up_statistics_trimmed:
                query = query.filter(ZtPool.limit_up_statistics == limit_up_statistics_trimmed)
            # 其他情况，使用模糊匹配
            else:
                query = query.filter(ZtPool.limit_up_statistics.like(f"%{limit_up_statistics_trimmed}%"))
        
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
                query = query.filter(ZtPool.stock_name.in_(stock_names))
            else:
                # 如果没有匹配的概念板块，返回空结果
                query = query.filter(ZtPool.id == -1)
        
        # 是否龙虎榜筛选（性能优化：使用子查询而不是先查询所有再过滤）
        if is_lhb is not None:
            # 使用子查询直接筛选，避免先查询所有龙虎榜股票
            lhb_date_filter = and_(
                LhbDetail.date >= start_date,
                LhbDetail.date <= end_date
            )
            
            lhb_subquery = db.query(LhbDetail.stock_code).filter(
                lhb_date_filter
            ).distinct().subquery()
            
            if is_lhb:
                # 只返回在龙虎榜中的股票（使用JOIN或EXISTS）
                query = query.join(
                    lhb_subquery,
                    ZtPool.stock_code == lhb_subquery.c.stock_code
                )
            else:
                # 只返回不在龙虎榜中的股票（使用NOT EXISTS）
                query = query.filter(
                    ~ZtPool.stock_code.in_(
                        db.query(LhbDetail.stock_code).filter(
                            lhb_date_filter
                        ).distinct()
                    )
                )
        
        # 排序
        if sort_by:
            sort_column = getattr(ZtPool, sort_by, None)
            if sort_column:
                if order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(ZtPool.change_percent))
        
        # 日期范围查询，需要统计涨停次数并去重
        # 先应用所有筛选条件构建基础查询
        base_query = query
        
        # 统计每个股票的涨停次数（只要存在记录就算一次）
        # 只统计日期范围内的总次数，不受其他筛选条件影响
        # 只受日期范围和股票代码/名称筛选影响，不受连板数、板数统计、行业、概念等筛选影响
        count_query = db.query(ZtPool).filter(
            ZtPool.date >= start_date,
            ZtPool.date <= end_date
        )
        
        # 只应用股票代码和股票名称筛选（因为这些是股票级别的筛选）
        if stock_code:
            count_query = count_query.filter(ZtPool.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            count_query = count_query.filter(ZtPool.stock_name.like(f"%{stock_name.strip()}%"))
        
        # 统计每个股票的涨停次数：每条记录算一次，只要存在记录就算一次
        # 使用 count(id) 统计每个股票在日期范围内的记录数（即涨停次数）
        limit_up_counts_query = count_query.order_by(None).with_entities(
            ZtPool.stock_code,
            func.count(ZtPool.id).label('limit_up_count')
        ).group_by(ZtPool.stock_code)
        
        limit_up_counts_dict = {
            row.stock_code: row.limit_up_count
            for row in limit_up_counts_query.all()
        }
        
        # 获取每个股票的最新记录（按日期倒序）
        # 使用窗口函数获取每个股票的最新记录
        from sqlalchemy import select
        
        # 为每个股票获取最新日期的记录ID（只应用日期范围和股票代码/名称筛选）
        latest_ids_base_query = db.query(ZtPool).filter(
            ZtPool.date >= start_date,
            ZtPool.date <= end_date
        )
        
        if stock_code:
            latest_ids_base_query = latest_ids_base_query.filter(ZtPool.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            latest_ids_base_query = latest_ids_base_query.filter(ZtPool.stock_name.like(f"%{stock_name.strip()}%"))
        
        latest_ids_subquery = latest_ids_base_query.with_entities(
            ZtPool.id,
            func.row_number().over(
                partition_by=ZtPool.stock_code,
                order_by=desc(ZtPool.date)
            ).label('rn')
        ).subquery()
        
        latest_ids = db.query(latest_ids_subquery.c.id).filter(
            latest_ids_subquery.c.rn == 1
        ).subquery()
        
        # 获取最新记录，并应用所有筛选条件
        items_query = base_query.filter(ZtPool.id.in_(select(latest_ids.c.id)))
        
        # 获取所有记录
        all_items = items_query.all()
        # 为每个记录添加涨停次数
        for item in all_items:
            setattr(item, 'limit_up_count', limit_up_counts_dict.get(item.stock_code, 0))
        
        # 排序
        if sort_by:
            sort_column = getattr(ZtPool, sort_by, None)
            if sort_column:
                # 有排序字段时，先按涨停次数排序，然后按指定字段排序
                all_items.sort(
                    key=lambda x: (
                        -getattr(x, 'limit_up_count', 0),
                        -(getattr(x, sort_by) or 0) if order == "desc" else (getattr(x, sort_by) or 0)
                    )
                )
        else:
            # 默认按涨停次数倒序，然后按涨跌幅倒序
            all_items.sort(
                key=lambda x: (
                    -getattr(x, 'limit_up_count', 0),
                    -(x.change_percent or 0)
                )
            )
        
        # 总数
        total = len(all_items)
        # 分页
        offset = (page - 1) * page_size
        items = all_items[offset:offset + page_size]
        
        # 批量查询龙虎榜股票代码集合和概念信息
        lhb_stock_codes = set()
        concepts_by_stock = {}
        
        if items:
            stock_codes = [item.stock_code for item in items]
            stock_names = [item.stock_name for item in items]
            
            # 批量查询龙虎榜股票代码（查询日期范围内的所有龙虎榜）
            lhb_details = db.query(LhbDetail.stock_code).filter(
                LhbDetail.date >= start_date,
                LhbDetail.date <= end_date,
                LhbDetail.stock_code.in_(stock_codes)
            ).distinct().all()
            lhb_stock_codes = {detail.stock_code for detail in lhb_details}
            
            # 批量查询所有股票的概念信息
            if stock_names:
                concepts_by_stock = StockConceptService.get_by_stock_names(
                    db=db,
                    stock_names=stock_names
                )
                
                for stock_name in stock_names:
                    if stock_name in concepts_by_stock:
                        concepts_by_stock[stock_name].sort(
                            key=lambda c: (c.level or 0, c.sort_order or 0, c.name or '')
                        )
        
        # 为每个涨停股添加是否在龙虎榜的标记和概念信息
        for item in items:
            setattr(item, 'is_lhb', item.stock_code in lhb_stock_codes)
            concepts = concepts_by_stock.get(item.stock_name, [])
            setattr(item, '_concepts', concepts)
        
        return items, total
    
    @staticmethod
    def get_concepts_for_zt_pool(db: Session, zt_pool: ZtPool) -> List:
        """获取涨停池记录的概念板块列表（包含层级信息）"""
        return StockConceptService.get_stock_concepts_with_hierarchy(db, zt_pool.stock_name)
    
    @staticmethod
    def get_zt_analysis(
        db: Session,
        target_date: date
    ) -> Dict:
        """
        获取涨停分析
        """
        query = db.query(ZtPool).filter(ZtPool.date == target_date)
        
        total_count = query.count()
        
        # 行业分布
        industry_dist = db.query(
            ZtPool.industry,
            func.count(ZtPool.id).label("count")
        ).filter(
            ZtPool.date == target_date
        ).group_by(ZtPool.industry).all()
        
        industry_distribution = {item[0]: item[1] for item in industry_dist if item[0]}
        
        # 概念分布（需要解析concept字段）
        all_concepts = {}
        items = query.all()
        for item in items:
            if item.concept:
                concepts = [c.strip() for c in item.concept.split(",") if c.strip()]
                for concept in concepts:
                    all_concepts[concept] = all_concepts.get(concept, 0) + 1
        
        concept_distribution = dict(sorted(all_concepts.items(), key=lambda x: x[1], reverse=True)[:20])
        
        # 原因分布
        reason_dist = db.query(
            ZtPool.limit_up_reason,
            func.count(ZtPool.id).label("count")
        ).filter(
            and_(
                ZtPool.date == target_date,
                ZtPool.limit_up_reason.isnot(None)
            )
        ).group_by(ZtPool.limit_up_reason).all()
        
        reason_distribution = {item[0]: item[1] for item in reason_dist if item[0]}
        
        # 连板数分布
        consecutive_dist = db.query(
            ZtPool.consecutive_limit_count,
            func.count(ZtPool.id).label("count")
        ).filter(
            ZtPool.date == target_date
        ).group_by(ZtPool.consecutive_limit_count).all()
        
        consecutive_limit_distribution = {str(item[0]): item[1] for item in consecutive_dist if item[0]}
        
        return {
            "total_count": total_count,
            "industry_distribution": industry_distribution,
            "concept_distribution": concept_distribution,
            "reason_distribution": reason_distribution,
            "consecutive_limit_distribution": consecutive_limit_distribution,
        }
    
    @staticmethod
    def get_concept_list(
        db: Session,
        target_date: date
    ) -> List[str]:
        """获取指定日期的概念列表"""
        items = db.query(ZtPool.concept).filter(
            and_(
                ZtPool.date == target_date,
                ZtPool.concept.isnot(None)
            )
        ).distinct().all()
        
        concepts = set()
        for item in items:
            if item[0]:
                concepts.update([c.strip() for c in item[0].split(",") if c.strip()])
        
        return sorted(list(concepts))
    
    @staticmethod
    def get_all_concepts(db: Session) -> List[str]:
        """获取所有历史概念列表"""
        items = db.query(ZtPool.concept).filter(
            ZtPool.concept.isnot(None),
            ZtPool.concept != ""
        ).distinct().all()
        
        concepts = set()
        for item in items:
            if item[0]:
                concepts.update([c.strip() for c in item[0].split(",") if c.strip()])
        
        return sorted(list(concepts))
    
    @staticmethod
    def save_zt_pool_data(
        db: Session,
        target_date: date,
        df: pd.DataFrame
    ) -> int:
        """
        保存涨停池数据
        保存 stock_zt_pool_em 接口返回的所有字段
        """
        # 打印所有列名用于调试
        if not df.empty:
            print(f"接口返回的列: {df.columns.tolist()}")
        
        count = 0
        for _, row in df.iterrows():
            stock_code = str(row.get("代码", "")).zfill(6)
            stock_name = row.get("名称", "")
            
            if not stock_code or not stock_name:
                print(f"警告: 跳过无效数据，代码={stock_code}, 名称={stock_name}")
                continue
            
            # 检查是否已存在
            existing = db.query(ZtPool).filter(
                and_(
                    ZtPool.date == target_date,
                    ZtPool.stock_code == stock_code
                )
            ).first()
            
            # 解析时间字段，支持多种格式
            first_limit_time = None
            last_limit_time = None
            
            # 首次封板时间
            first_time_str = row.get("首次封板时间")
            if first_time_str:
                try:
                    from datetime import datetime
                    first_time_str = str(first_time_str).strip()
                    # 尝试多种时间格式
                    for fmt in ["%H:%M:%S", "%H:%M", "%H:%M:%S.%f"]:
                        try:
                            first_limit_time = datetime.strptime(first_time_str, fmt).time()
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"解析首次封板时间失败: {first_time_str}, 错误: {e}")
            
            # 最后封板时间
            last_time_str = row.get("最后封板时间")
            if last_time_str:
                try:
                    from datetime import datetime
                    last_time_str = str(last_time_str).strip()
                    # 尝试多种时间格式
                    for fmt in ["%H:%M:%S", "%H:%M", "%H:%M:%S.%f"]:
                        try:
                            last_limit_time = datetime.strptime(last_time_str, fmt).time()
                            break
                        except ValueError:
                            continue
                except Exception as e:
                    print(f"解析最后封板时间失败: {last_time_str}, 错误: {e}")
            
            # 构建数据字典，保存所有可用字段
            data = {
                "date": target_date,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "change_percent": safe_float(row.get("涨跌幅")),
                "latest_price": safe_float(row.get("最新价")),
                "turnover_amount": safe_int(row.get("成交额")),
                "circulation_market_value": safe_float(row.get("流通市值")),
                "total_market_value": safe_float(row.get("总市值")),
                "turnover_rate": safe_float(row.get("换手率")),
                "limit_up_capital": safe_int(row.get("封板资金")),
                "first_limit_time": first_limit_time,
                "last_limit_time": last_limit_time,
                "explosion_count": safe_int(row.get("炸板次数")) or 0,
                "limit_up_statistics": str(row.get("涨停统计", "")),
                "consecutive_limit_count": safe_int(row.get("连板数")) or 1,
                "industry": str(row.get("所属行业", "")),
                "concept": str(row.get("概念", "")),
                "limit_up_reason": str(row.get("涨停原因", "")),
            }
            
            # 保存所有数据，包括更新已存在的记录
            if existing:
                # 更新所有字段
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                # 创建新记录
                zt = ZtPool(**data)
                db.add(zt)
            
            count += 1
        
        # 提交所有更改
        db.commit()
        print(f"成功保存 {count} 条涨停池数据到数据库")
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date):
        """
        同步涨停池数据
        从AKShare获取数据并保存到数据库
        使用接口: stock_zt_pool_em
        保存接口返回的所有字段数据
        """
        from app.utils.sync_result import SyncResult
        
        try:
            # 支持按日期获取（YYYYMMDD），未传则为当日
            date_str = target_date.strftime("%Y%m%d") if target_date else None
            print(f"开始同步 {target_date} 的涨停池数据，日期参数: {date_str}")
            
            df = safe_akshare_call(ak.stock_zt_pool_em, date=date_str)
            
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的涨停池数据，可能该日期无涨停股票或接口无数据"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")
            
            # 打印数据框信息用于调试
            print(f"获取到 {len(df)} 条数据，列数: {len(df.columns)}")
            print(f"数据列名: {df.columns.tolist()}")
            
            # 保存所有数据
            count = ZtPoolService.save_zt_pool_data(db, target_date, df)
            
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的涨停池数据，共 {count} 条")
            return SyncResult.success_result(f"涨停池数据同步成功，共保存 {count} 条记录", count)
        except Exception as e:
            error_msg = f"同步涨停池数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)

    @staticmethod
    def update_fields(db: Session, record_id: int, concept: Optional[str], limit_up_reason: Optional[str]) -> Optional[ZtPool]:
        """更新涨停池可编辑字段"""
        rec = db.query(ZtPool).filter(ZtPool.id == record_id).first()
        if not rec:
            return None
        if concept is not None:
            rec.concept = concept
        if limit_up_reason is not None:
            rec.limit_up_reason = limit_up_reason
        db.commit()
        db.refresh(rec)
        return rec


class ZtPoolDownService:
    """跌停池服务类（stock_zt_pool_dtgc_em）"""

    @staticmethod
    def get_list(
        db: Session,
        target_date: date,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        concept: Optional[str] = None,
        industry: Optional[str] = None,
        consecutive_limit_count: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "asc",  # 跌停默认升序（跌幅更大在前）
    ) -> tuple[List[ZtPoolDown], int]:
        query = db.query(ZtPoolDown).filter(ZtPoolDown.date == target_date)

        if stock_code:
            query = query.filter(ZtPoolDown.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            query = query.filter(ZtPoolDown.stock_name.like(f"%{stock_name.strip()}%"))
        if concept:
            query = query.filter(ZtPoolDown.concept.like(f"%{concept}%"))
        if industry:
            query = query.filter(ZtPoolDown.industry == industry)
        if consecutive_limit_count is not None:
            query = query.filter(ZtPoolDown.consecutive_limit_count == consecutive_limit_count)

        if sort_by:
            col = getattr(ZtPoolDown, sort_by, None)
            if col is not None:
                query = query.order_by(col.asc() if order == "asc" else col.desc())
        else:
            query = query.order_by(asc(ZtPoolDown.change_percent))

        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # 为每个跌停股加载概念板块
        for item in items:
            concepts = StockConceptService.get_by_stock_name(db, item.stock_name)
            setattr(item, '_concepts', concepts)
        
        return items, total

    @staticmethod
    def get_list_by_date_range(
        db: Session,
        start_date: date,
        end_date: date,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        concept: Optional[str] = None,
        industry: Optional[str] = None,
        consecutive_limit_count: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "asc",
    ) -> tuple[List[ZtPoolDown], int]:
        """
        获取日期范围内的跌停池列表（按股票代码聚合）
        
        对于多日查询，会按股票代码分组并聚合数据：
        - 统计每个股票的跌停次数（每条记录算一次）
        - 获取每个股票的最新记录
        """
        # 使用日期范围查询
        query = db.query(ZtPoolDown).filter(
            ZtPoolDown.date >= start_date,
            ZtPoolDown.date <= end_date
        )
        
        if stock_code:
            query = query.filter(ZtPoolDown.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            query = query.filter(ZtPoolDown.stock_name.like(f"%{stock_name.strip()}%"))
        
        if concept:
            query = query.filter(ZtPoolDown.concept.like(f"%{concept}%"))
        
        if industry:
            query = query.filter(ZtPoolDown.industry == industry)
        
        if consecutive_limit_count is not None:
            query = query.filter(ZtPoolDown.consecutive_limit_count == consecutive_limit_count)
        
        # 排序
        if sort_by:
            col = getattr(ZtPoolDown, sort_by, None)
            if col is not None:
                query = query.order_by(col.asc() if order == "asc" else col.desc())
        else:
            query = query.order_by(asc(ZtPoolDown.change_percent))
        
        # 日期范围查询，需要统计跌停次数并去重
        base_query = query
        
        # 统计每个股票的跌停次数（只要存在记录就算一次）
        # 只统计日期范围内的总次数，不受其他筛选条件影响
        count_query = db.query(ZtPoolDown).filter(
            ZtPoolDown.date >= start_date,
            ZtPoolDown.date <= end_date
        )
        
        # 只应用股票代码和股票名称筛选
        if stock_code:
            count_query = count_query.filter(ZtPoolDown.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            count_query = count_query.filter(ZtPoolDown.stock_name.like(f"%{stock_name.strip()}%"))
        
        # 统计每个股票的跌停次数：每条记录算一次
        limit_down_counts_query = count_query.order_by(None).with_entities(
            ZtPoolDown.stock_code,
            func.count(ZtPoolDown.id).label('limit_down_count')
        ).group_by(ZtPoolDown.stock_code)
        
        limit_down_counts_dict = {
            row.stock_code: row.limit_down_count
            for row in limit_down_counts_query.all()
        }
        
        # 获取每个股票的最新记录（按日期倒序）
        from sqlalchemy import select
        
        # 为每个股票获取最新日期的记录ID
        latest_ids_base_query = db.query(ZtPoolDown).filter(
            ZtPoolDown.date >= start_date,
            ZtPoolDown.date <= end_date
        )
        
        if stock_code:
            latest_ids_base_query = latest_ids_base_query.filter(ZtPoolDown.stock_code == stock_code)
        
        if stock_name and stock_name.strip():
            latest_ids_base_query = latest_ids_base_query.filter(ZtPoolDown.stock_name.like(f"%{stock_name.strip()}%"))
        
        latest_ids_subquery = latest_ids_base_query.with_entities(
            ZtPoolDown.id,
            func.row_number().over(
                partition_by=ZtPoolDown.stock_code,
                order_by=desc(ZtPoolDown.date)
            ).label('rn')
        ).subquery()
        
        latest_ids = db.query(latest_ids_subquery.c.id).filter(
            latest_ids_subquery.c.rn == 1
        ).subquery()
        
        # 获取最新记录，并应用所有筛选条件
        items_query = base_query.filter(ZtPoolDown.id.in_(select(latest_ids.c.id)))
        
        # 获取所有记录
        all_items = items_query.all()
        
        # 为每个记录添加跌停次数
        for item in all_items:
            setattr(item, 'limit_up_count', limit_down_counts_dict.get(item.stock_code, 0))  # 使用limit_up_count字段名保持一致性
        
        # 排序
        if sort_by:
            col = getattr(ZtPoolDown, sort_by, None)
            if col is not None:
                # 有排序字段时，先按跌停次数排序，然后按指定字段排序
                all_items.sort(
                    key=lambda x: (
                        -getattr(x, 'limit_up_count', 0),
                        (getattr(x, sort_by) or 0) if order == "asc" else -(getattr(x, sort_by) or 0)
                    )
                )
        else:
            # 默认按跌停次数倒序，然后按涨跌幅升序（跌幅更大在前）
            all_items.sort(
                key=lambda x: (
                    -getattr(x, 'limit_up_count', 0),
                    (x.change_percent or 0)
                )
            )
        
        # 总数
        total = len(all_items)
        # 分页
        offset = (page - 1) * page_size
        items = all_items[offset:offset + page_size]
        
        # 为每个跌停股加载概念板块
        for item in items:
            concepts = StockConceptService.get_by_stock_name(db, item.stock_name)
            setattr(item, '_concepts', concepts)
        
        return items, total

    @staticmethod
    def save_data(db: Session, target_date: date, df: pd.DataFrame) -> int:
        count = 0
        for _, row in df.iterrows():
            stock_code = str(row.get("代码", "")).zfill(6)
            stock_name = row.get("名称", "")
            if not stock_code or not stock_name:
                continue

            existing = db.query(ZtPoolDown).filter(
                and_(ZtPoolDown.date == target_date, ZtPoolDown.stock_code == stock_code)
            ).first()

            first_limit_time = None
            last_limit_time = None
            if row.get("首次封板时间"):
                try:
                    from datetime import datetime
                    first_limit_time = datetime.strptime(str(row.get("首次封板时间")), "%H:%M:%S").time()
                except:
                    pass
            if row.get("最后封板时间"):
                try:
                    from datetime import datetime
                    last_limit_time = datetime.strptime(str(row.get("最后封板时间")), "%H:%M:%S").time()
                except:
                    pass

            data = {
                "date": target_date,
                "stock_code": stock_code,
                "stock_name": stock_name,
                "change_percent": safe_float(row.get("涨跌幅")),
                "latest_price": safe_float(row.get("最新价")),
                "turnover_amount": safe_int(row.get("成交额")),
                "circulation_market_value": safe_float(row.get("流通市值")),
                "total_market_value": safe_float(row.get("总市值")),
                "turnover_rate": safe_float(row.get("换手率")),
                "limit_up_capital": safe_int(row.get("封板资金")),
                "first_limit_time": first_limit_time,
                "last_limit_time": last_limit_time,
                "explosion_count": safe_int(row.get("炸板次数")) or 0,
                "limit_up_statistics": str(row.get("涨停统计", "")),
                "consecutive_limit_count": safe_int(row.get("连板数")) or 1,
                "industry": str(row.get("所属行业", "")),
                "concept": str(row.get("概念", "")),
                "limit_up_reason": str(row.get("涨停原因", row.get("跌停原因", ""))),
            }

            if existing:
                for k, v in data.items():
                    setattr(existing, k, v)
            else:
                rec = ZtPoolDown(**data)
                db.add(rec)
            count += 1

        db.commit()
        return count

    @staticmethod
    def sync_data(db: Session, target_date: date):
        from app.utils.sync_result import SyncResult
        
        try:
            date_str = target_date.strftime("%Y%m%d") if target_date else None
            df = safe_akshare_call(ak.stock_zt_pool_dtgc_em, date=date_str)
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的跌停池数据，可能该日期无跌停股票或接口无数据"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")
            
            count = ZtPoolDownService.save_data(db, target_date, df)
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的跌停池数据，共 {count} 条")
            return SyncResult.success_result(f"跌停池数据同步成功", count)
        except Exception as e:
            error_msg = f"同步跌停池数据失败: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            return SyncResult.failure_result(str(e), error_msg)

