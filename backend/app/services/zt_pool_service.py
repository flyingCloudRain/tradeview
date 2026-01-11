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
from app.utils.akshare_utils import safe_akshare_call
from app.utils.format_utils import safe_float, safe_int
import akshare as ak


class ZtPoolService:
    """涨停池服务类"""
    
    @staticmethod
    def get_zt_pool_list(
        db: Session,
        target_date: date,
        stock_code: Optional[str] = None,
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
            is_lhb: 是否龙虎榜筛选，True表示只返回龙虎榜股票，False表示只返回非龙虎榜股票，None表示不筛选
        """
        query = db.query(ZtPool).filter(ZtPool.date == target_date)
        
        if stock_code:
            query = query.filter(ZtPool.stock_code == stock_code)
        
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
        
        # 是否龙虎榜筛选
        if is_lhb is not None:
            # 查询当日所有龙虎榜股票代码
            lhb_stock_codes_query = db.query(LhbDetail.stock_code).filter(
                LhbDetail.date == target_date
            ).distinct()
            lhb_stock_codes = {row[0] for row in lhb_stock_codes_query.all()}
            
            if is_lhb:
                # 只返回在龙虎榜中的股票
                if lhb_stock_codes:
                    query = query.filter(ZtPool.stock_code.in_(lhb_stock_codes))
                else:
                    # 如果没有龙虎榜数据，返回空结果
                    query = query.filter(ZtPool.id == -1)
            else:
                # 只返回不在龙虎榜中的股票
                if lhb_stock_codes:
                    query = query.filter(~ZtPool.stock_code.in_(lhb_stock_codes))
        
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
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        # 查询当日龙虎榜股票代码集合（用于标记）
        lhb_stock_codes = set()
        if items:
            stock_codes = [item.stock_code for item in items]
            lhb_details = db.query(LhbDetail.stock_code).filter(
                LhbDetail.date == target_date,
                LhbDetail.stock_code.in_(stock_codes)
            ).all()
            lhb_stock_codes = {detail.stock_code for detail in lhb_details}
        
        # 为每个涨停股添加是否在龙虎榜的标记
        for item in items:
            setattr(item, 'is_lhb', item.stock_code in lhb_stock_codes)
        
        # 为每个涨停股加载概念板块
        from app.services.stock_concept_service import StockConceptService
        for item in items:
            concepts = StockConceptService.get_by_stock_name(db, item.stock_name)
            setattr(item, '_concepts', concepts)
        
        return items, total
    
    @staticmethod
    def get_concepts_for_zt_pool(db: Session, zt_pool: ZtPool) -> List:
        """获取涨停池记录的概念板块列表"""
        from app.services.stock_concept_service import StockConceptService
        return StockConceptService.get_by_stock_name(db, zt_pool.stock_name)
    
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
        """
        count = 0
        for _, row in df.iterrows():
            stock_code = str(row.get("代码", "")).zfill(6)
            stock_name = row.get("名称", "")
            
            # 检查是否已存在
            existing = db.query(ZtPool).filter(
                and_(
                    ZtPool.date == target_date,
                    ZtPool.stock_code == stock_code
                )
            ).first()
            
            # 解析时间
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
                "limit_up_reason": str(row.get("涨停原因", "")),
            }
            
            if existing:
                for key, value in data.items():
                    setattr(existing, key, value)
            else:
                zt = ZtPool(**data)
                db.add(zt)
            
            count += 1
        
        db.commit()
        return count
    
    @staticmethod
    def sync_data(db: Session, target_date: date):
        """
        同步涨停池数据
        从AKShare获取数据并保存到数据库
        使用接口: stock_zt_pool_em
        """
        from app.utils.sync_result import SyncResult
        
        try:
            # 支持按日期获取（YYYYMMDD），未传则为当日
            date_str = target_date.strftime("%Y%m%d") if target_date else None
            df = safe_akshare_call(ak.stock_zt_pool_em, date=date_str)
            
            if df is None or df.empty:
                error_msg = f"未获取到 {target_date} 的涨停池数据，可能该日期无涨停股票或接口无数据"
                print(error_msg)
                return SyncResult.failure_result(error_msg, "数据源返回空")
            
            count = ZtPoolService.save_zt_pool_data(db, target_date, df)
            if count == 0:
                return SyncResult.failure_result("保存数据失败，保存数量为0", "数据库保存异常")
            
            print(f"成功同步 {target_date} 的涨停池数据，共 {count} 条")
            return SyncResult.success_result(f"涨停池数据同步成功", count)
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
        from app.services.stock_concept_service import StockConceptService
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

