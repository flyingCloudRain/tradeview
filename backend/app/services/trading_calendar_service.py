"""
交易日历服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from typing import Optional, List
from datetime import date
import math

from app.models.trading_calendar import TradingCalendar
from app.models.stock_concept import StockConceptMapping, TradingCalendarConcept
from app.config import settings


class TradingCalendarService:
    """交易日历服务类"""
    
    @staticmethod
    def get_list(
        db: Session,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        stock_name: Optional[str] = None,
        direction: Optional[str] = None,
        strategy: Optional[str] = None,
        source: Optional[str] = None,
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[TradingCalendar], int]:
        """获取交易日历列表"""
        query = db.query(TradingCalendar)
        
        # 日期范围过滤
        if start_date:
            query = query.filter(TradingCalendar.date >= start_date)
        if end_date:
            query = query.filter(TradingCalendar.date <= end_date)
        
        # 股票名称模糊查询
        if stock_name and stock_name.strip():
            stock_name_clean = stock_name.strip()
            query = query.filter(
                func.lower(TradingCalendar.stock_name).like(f"%{stock_name_clean.lower()}%")
            )
        
        # 操作方向过滤
        if direction:
            query = query.filter(TradingCalendar.direction == direction)
        
        # 策略过滤
        if strategy:
            query = query.filter(TradingCalendar.strategy == strategy)
        
        # 来源过滤
        if source and source.strip():
            source_clean = source.strip()
            query = query.filter(TradingCalendar.source == source_clean)
        
        # 概念板块过滤
        if concept_ids or concept_names:
            # 构建子查询：获取符合概念板块条件的股票名称
            from app.models.stock_concept import StockConcept
            
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
            
            # 同时检查交易日历专用关联表
            calendar_concept_subquery = db.query(TradingCalendarConcept.trading_calendar_id).distinct()
            
            if concept_ids:
                calendar_concept_subquery = calendar_concept_subquery.filter(
                    TradingCalendarConcept.concept_id.in_(concept_ids)
                )
            
            if concept_names:
                calendar_concept_subquery = calendar_concept_subquery.join(
                    StockConcept,
                    TradingCalendarConcept.concept_id == StockConcept.id
                ).filter(
                    StockConcept.name.in_(concept_names)
                )
            
            # 合并两个条件：股票名称匹配或交易日历ID匹配
            stock_names = [row[0] for row in concept_subquery.all()]
            calendar_ids = [row[0] for row in calendar_concept_subquery.all()]
            
            if stock_names or calendar_ids:
                from sqlalchemy import or_
                conditions = []
                if stock_names:
                    conditions.append(TradingCalendar.stock_name.in_(stock_names))
                if calendar_ids:
                    conditions.append(TradingCalendar.id.in_(calendar_ids))
                query = query.filter(or_(*conditions))
            else:
                # 如果没有匹配的概念板块，返回空结果
                query = query.filter(TradingCalendar.id == -1)
        
        # 排序
        if sort_by:
            sort_column = getattr(TradingCalendar, sort_by, None)
            if sort_column:
                if order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                # 默认排序：日期倒序，然后按来源、操作方向、策略、个股
                # 使用 coalesce 处理 NULL 值，确保 NULL 排在最后
                query = query.order_by(
                    TradingCalendar.date.desc(),  # 日期倒序（最新在前）
                    func.coalesce(TradingCalendar.source, 'zzz').asc(),  # NULL 值用 'zzz' 替代，确保排在最后
                    TradingCalendar.direction.asc(),
                    TradingCalendar.strategy.asc(),
                    TradingCalendar.stock_name.asc(),
                    TradingCalendar.id.desc()
                )
        else:
            # 默认排序：日期倒序，然后按来源、操作方向、策略、个股
            # 使用 coalesce 处理 NULL 值，确保 NULL 排在最后
            query = query.order_by(
                TradingCalendar.date.desc(),  # 日期倒序（最新在前）
                func.coalesce(TradingCalendar.source, 'zzz').asc(),  # NULL 值用 'zzz' 替代，确保排在最后
                TradingCalendar.direction.asc(),
                TradingCalendar.strategy.asc(),
                TradingCalendar.stock_name.asc(),
                TradingCalendar.id.desc()
            )
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def get_by_id(db: Session, calendar_id: int) -> Optional[TradingCalendar]:
        """根据ID获取交易日历"""
        return db.query(TradingCalendar).filter(TradingCalendar.id == calendar_id).first()
    
    @staticmethod
    def get_concepts_for_calendar(db: Session, calendar: TradingCalendar) -> List:
        """获取交易日历的概念板块列表（优先使用记录级关联，其次使用股票名称关联）"""
        from app.models.stock_concept import StockConcept
        
        # 1. 先查询记录级别的概念板块关联
        record_concepts = db.query(StockConcept).join(
            TradingCalendarConcept,
            StockConcept.id == TradingCalendarConcept.concept_id
        ).filter(
            TradingCalendarConcept.trading_calendar_id == calendar.id
        ).all()
        
        if record_concepts:
            return record_concepts
        
        # 2. 如果没有记录级别的关联，使用股票名称的通用关联
        return db.query(StockConcept).join(
            StockConceptMapping,
            StockConcept.id == StockConceptMapping.concept_id
        ).filter(
            StockConceptMapping.stock_name == calendar.stock_name
        ).all()
    
    @staticmethod
    def create(db: Session, calendar_data: dict) -> TradingCalendar:
        """创建交易日历"""
        calendar = TradingCalendar(**calendar_data)
        db.add(calendar)
        db.commit()
        db.refresh(calendar)
        return calendar
    
    @staticmethod
    def update(db: Session, calendar_id: int, update_data: dict) -> Optional[TradingCalendar]:
        """更新交易日历"""
        calendar = db.query(TradingCalendar).filter(TradingCalendar.id == calendar_id).first()
        if not calendar:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(calendar, key, value)
        
        db.commit()
        db.refresh(calendar)
        return calendar
    
    @staticmethod
    def delete(db: Session, calendar_id: int) -> bool:
        """删除交易日历"""
        calendar = db.query(TradingCalendar).filter(TradingCalendar.id == calendar_id).first()
        if not calendar:
            return False
        
        db.delete(calendar)
        db.commit()
        return True

