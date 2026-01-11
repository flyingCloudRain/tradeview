"""
股票概念板块服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional, List
import math

from app.models.stock_concept import StockConcept, StockConceptMapping
from app.config import settings


class StockConceptService:
    """股票概念板块服务类"""
    
    @staticmethod
    def get_list(
        db: Session,
        name: Optional[str] = None,
        code: Optional[str] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[List[StockConcept], int]:
        """获取概念板块列表"""
        query = db.query(StockConcept)
        
        # 名称模糊查询
        if name and name.strip():
            name_clean = name.strip()
            query = query.filter(
                func.lower(StockConcept.name).like(f"%{name_clean.lower()}%")
            )
        
        # 代码精确查询
        if code and code.strip():
            query = query.filter(StockConcept.code == code.strip())
        
        # 排序：按名称
        query = query.order_by(StockConcept.name.asc())
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def get_by_id(db: Session, concept_id: int) -> Optional[StockConcept]:
        """根据ID获取概念板块"""
        return db.query(StockConcept).filter(StockConcept.id == concept_id).first()
    
    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[StockConcept]:
        """根据名称获取概念板块"""
        return db.query(StockConcept).filter(StockConcept.name == name).first()
    
    @staticmethod
    def create(db: Session, concept_data: dict) -> StockConcept:
        """创建概念板块"""
        concept = StockConcept(**concept_data)
        db.add(concept)
        db.commit()
        db.refresh(concept)
        return concept
    
    @staticmethod
    def update(db: Session, concept_id: int, update_data: dict) -> Optional[StockConcept]:
        """更新概念板块"""
        concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        if not concept:
            return None
        
        for key, value in update_data.items():
            if value is not None:
                setattr(concept, key, value)
        
        db.commit()
        db.refresh(concept)
        return concept
    
    @staticmethod
    def delete(db: Session, concept_id: int) -> bool:
        """删除概念板块"""
        concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        if not concept:
            return False
        
        db.delete(concept)
        db.commit()
        return True
    
    @staticmethod
    def get_by_stock_name(db: Session, stock_name: str) -> List[StockConcept]:
        """根据股票名称获取概念板块列表"""
        return db.query(StockConcept).join(
            StockConceptMapping,
            StockConcept.id == StockConceptMapping.concept_id
        ).filter(
            StockConceptMapping.stock_name == stock_name
        ).all()
    
    @staticmethod
    def get_by_stock_names(db: Session, stock_names: List[str]) -> dict[str, List[StockConcept]]:
        """批量查询股票的概念板块"""
        if not stock_names:
            return {}
        
        mappings = db.query(StockConceptMapping).filter(
            StockConceptMapping.stock_name.in_(stock_names)
        ).all()
        
        concept_ids = [m.concept_id for m in mappings]
        concepts = {}
        if concept_ids:
            concept_list = db.query(StockConcept).filter(
                StockConcept.id.in_(concept_ids)
            ).all()
            concept_dict = {c.id: c for c in concept_list}
            
            for mapping in mappings:
                if mapping.stock_name not in concepts:
                    concepts[mapping.stock_name] = []
                if mapping.concept_id in concept_dict:
                    concepts[mapping.stock_name].append(concept_dict[mapping.concept_id])
        
        # 确保所有股票都有条目（即使为空列表）
        for stock_name in stock_names:
            if stock_name not in concepts:
                concepts[stock_name] = []
        
        return concepts


class StockConceptMappingService:
    """股票概念板块关联服务类"""
    
    @staticmethod
    def set_concepts_for_stock(
        db: Session,
        stock_name: str,
        concept_ids: List[int]
    ) -> List[StockConcept]:
        """为股票设置概念板块（替换所有现有关联）"""
        # 删除现有关联
        db.query(StockConceptMapping).filter(
            StockConceptMapping.stock_name == stock_name
        ).delete()
        
        # 创建新关联
        concepts = []
        for concept_id in concept_ids:
            # 检查概念是否存在
            concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
            if concept:
                mapping = StockConceptMapping(
                    stock_name=stock_name,
                    concept_id=concept_id
                )
                db.add(mapping)
                concepts.append(concept)
        
        db.commit()
        return concepts
    
    @staticmethod
    def add_concept_to_stock(
        db: Session,
        stock_name: str,
        concept_id: int
    ) -> Optional[StockConcept]:
        """为股票添加概念板块"""
        # 检查是否已存在
        existing = db.query(StockConceptMapping).filter(
            StockConceptMapping.stock_name == stock_name,
            StockConceptMapping.concept_id == concept_id
        ).first()
        
        if existing:
            return db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        
        # 检查概念是否存在
        concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        if not concept:
            return None
        
        mapping = StockConceptMapping(
            stock_name=stock_name,
            concept_id=concept_id
        )
        db.add(mapping)
        db.commit()
        return concept
    
    @staticmethod
    def remove_concept_from_stock(
        db: Session,
        stock_name: str,
        concept_id: int
    ) -> bool:
        """从股票移除概念板块"""
        mapping = db.query(StockConceptMapping).filter(
            StockConceptMapping.stock_name == stock_name,
            StockConceptMapping.concept_id == concept_id
        ).first()
        
        if not mapping:
            return False
        
        db.delete(mapping)
        db.commit()
        return True
    
    @staticmethod
    def get_stock_concepts(db: Session, stock_name: str) -> List[StockConcept]:
        """获取股票的概念板块列表"""
        return StockConceptService.get_by_stock_name(db, stock_name)
    
    @staticmethod
    def get_all_mappings(
        db: Session,
        stock_name: Optional[str] = None,
        concept_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 100,
    ) -> tuple[List[StockConceptMapping], int]:
        """获取所有关联关系"""
        query = db.query(StockConceptMapping)
        
        if stock_name:
            query = query.filter(StockConceptMapping.stock_name == stock_name)
        if concept_id:
            query = query.filter(StockConceptMapping.concept_id == concept_id)
        
        query = query.order_by(StockConceptMapping.stock_name.asc())
        
        total = query.count()
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total


class TradingCalendarConceptService:
    """交易日历概念板块关联服务类"""
    
    @staticmethod
    def set_concepts_for_calendar(
        db: Session,
        calendar_id: int,
        concept_ids: List[int]
    ) -> List[StockConcept]:
        """为交易日历设置概念板块（替换所有现有关联）"""
        from app.models.stock_concept import TradingCalendarConcept
        
        # 检查交易日历是否存在
        from app.models.trading_calendar import TradingCalendar
        calendar = db.query(TradingCalendar).filter(TradingCalendar.id == calendar_id).first()
        if not calendar:
            return []
        
        # 删除现有关联
        db.query(TradingCalendarConcept).filter(
            TradingCalendarConcept.trading_calendar_id == calendar_id
        ).delete()
        
        # 创建新关联
        concepts = []
        for concept_id in concept_ids:
            # 检查概念是否存在
            concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
            if concept:
                mapping = TradingCalendarConcept(
                    trading_calendar_id=calendar_id,
                    concept_id=concept_id
                )
                db.add(mapping)
                concepts.append(concept)
        
        db.commit()
        return concepts
    
    @staticmethod
    def add_concept_to_calendar(
        db: Session,
        calendar_id: int,
        concept_id: int
    ) -> Optional[StockConcept]:
        """为交易日历添加概念板块"""
        from app.models.stock_concept import TradingCalendarConcept
        
        # 检查是否已存在
        existing = db.query(TradingCalendarConcept).filter(
            TradingCalendarConcept.trading_calendar_id == calendar_id,
            TradingCalendarConcept.concept_id == concept_id
        ).first()
        
        if existing:
            return db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        
        # 检查概念是否存在
        concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        if not concept:
            return None
        
        mapping = TradingCalendarConcept(
            trading_calendar_id=calendar_id,
            concept_id=concept_id
        )
        db.add(mapping)
        db.commit()
        return concept
    
    @staticmethod
    def remove_concept_from_calendar(
        db: Session,
        calendar_id: int,
        concept_id: int
    ) -> bool:
        """从交易日历移除概念板块"""
        from app.models.stock_concept import TradingCalendarConcept
        
        mapping = db.query(TradingCalendarConcept).filter(
            TradingCalendarConcept.trading_calendar_id == calendar_id,
            TradingCalendarConcept.concept_id == concept_id
        ).first()
        
        if not mapping:
            return False
        
        db.delete(mapping)
        db.commit()
        return True
    
    @staticmethod
    def get_calendar_concepts(db: Session, calendar_id: int) -> List[StockConcept]:
        """获取交易日历的概念板块列表（仅记录级关联）"""
        from app.models.stock_concept import TradingCalendarConcept
        
        return db.query(StockConcept).join(
            TradingCalendarConcept,
            StockConcept.id == TradingCalendarConcept.concept_id
        ).filter(
            TradingCalendarConcept.trading_calendar_id == calendar_id
        ).all()
