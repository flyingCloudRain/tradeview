"""
交易日历服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func
from typing import Optional, List
from datetime import date
import math

from app.models.trading_calendar import TradingCalendar
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
        
        # 排序
        if sort_by:
            sort_column = getattr(TradingCalendar, sort_by, None)
            if sort_column:
                if order == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            else:
                # 默认按日期倒序
                query = query.order_by(desc(TradingCalendar.date), desc(TradingCalendar.id))
        else:
            # 默认按日期倒序
            query = query.order_by(desc(TradingCalendar.date), desc(TradingCalendar.id))
        
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

