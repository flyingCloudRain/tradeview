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
        level: Optional[int] = None,
        parent_id: Optional[int] = None,
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
        
        # 层级筛选
        if level is not None:
            query = query.filter(StockConcept.level == level)
        
        # 父概念筛选
        if parent_id is not None:
            query = query.filter(StockConcept.parent_id == parent_id)
        
        # 排序：按层级、排序顺序、名称
        query = query.order_by(
            StockConcept.level.asc(),
            StockConcept.sort_order.asc(),
            StockConcept.name.asc()
        )
        
        # 总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()
        
        return items, total
    
    @staticmethod
    def get_tree(db: Session, max_level: int = 3) -> List[StockConcept]:
        """获取概念树形结构"""
        # 查询所有一级概念
        level1_concepts = db.query(StockConcept).filter(
            StockConcept.level == 1
        ).order_by(
            StockConcept.sort_order.asc(),
            StockConcept.name.asc()
        ).all()
        
        return level1_concepts
    
    @staticmethod
    def expand_concept_ids(
        db: Session,
        concept_ids: List[int],
        include_descendants: bool = True,
        include_ancestors: bool = False
    ) -> List[int]:
        """
        扩展概念ID列表（包含子概念或父概念）
        
        Args:
            db: 数据库会话
            concept_ids: 原始概念ID列表
            include_descendants: 是否包含子概念
            include_ancestors: 是否包含父概念
            
        Returns:
            扩展后的概念ID列表
        """
        if not concept_ids:
            return []
        
        expanded_ids = set(concept_ids)
        
        # 查询所有相关概念
        concepts = db.query(StockConcept).filter(
            StockConcept.id.in_(concept_ids)
        ).all()
        
        for concept in concepts:
            # 包含子概念
            if include_descendants:
                descendants = StockConceptService.get_all_descendant_ids(db, concept.id)
                expanded_ids.update(descendants)
            
            # 包含父概念
            if include_ancestors:
                ancestors = StockConceptService.get_all_ancestor_ids(db, concept.id)
                expanded_ids.update(ancestors)
        
        return list(expanded_ids)
    
    @staticmethod
    def get_all_descendant_ids(db: Session, concept_id: int) -> List[int]:
        """获取所有子概念ID（递归）"""
        descendant_ids = []
        
        # 查询直接子概念
        children = db.query(StockConcept).filter(
            StockConcept.parent_id == concept_id
        ).all()
        
        for child in children:
            descendant_ids.append(child.id)
            # 递归查询子概念的子概念
            descendant_ids.extend(
                StockConceptService.get_all_descendant_ids(db, child.id)
            )
        
        return descendant_ids
    
    @staticmethod
    def get_all_ancestor_ids(db: Session, concept_id: int) -> List[int]:
        """获取所有父概念ID（向上递归）"""
        ancestor_ids = []
        
        concept = db.query(StockConcept).filter(
            StockConcept.id == concept_id
        ).first()
        
        if concept and concept.parent_id:
            ancestor_ids.append(concept.parent_id)
            # 递归查询父概念的父概念
            ancestor_ids.extend(
                StockConceptService.get_all_ancestor_ids(db, concept.parent_id)
            )
        
        return ancestor_ids
    
    @staticmethod
    def get_stock_concepts_with_hierarchy(
        db: Session,
        stock_name: str
    ) -> List[StockConcept]:
        """
        获取个股关联的所有概念（包含层级信息）
        
        Args:
            db: 数据库会话
            stock_name: 股票名称
            
        Returns:
            概念列表（包含层级信息，按层级和排序顺序排序）
        """
        concepts = db.query(StockConcept).join(
            StockConceptMapping,
            StockConceptMapping.concept_id == StockConcept.id
        ).filter(
            StockConceptMapping.stock_name == stock_name
        ).order_by(
            StockConcept.level.asc(),
            StockConcept.sort_order.asc(),
            StockConcept.name.asc()
        ).all()
        
        return concepts
    
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
        """创建概念板块（自动计算path和level）"""
        # 处理空字符串：将空字符串转换为 None，避免违反唯一约束
        if 'code' in concept_data and concept_data['code'] == '':
            concept_data['code'] = None
        if 'description' in concept_data and concept_data['description'] == '':
            concept_data['description'] = None
        
        # 如果指定了 parent_id，验证父概念存在并设置level
        parent_id = concept_data.get('parent_id')
        if parent_id:
            parent = db.query(StockConcept).filter(
                StockConcept.id == parent_id
            ).first()
            if not parent:
                raise ValueError("父概念不存在")
            # 设置level为父概念的level + 1
            concept_data['level'] = parent.level + 1
            if concept_data['level'] > 3:
                raise ValueError("层级不能超过3级")
        else:
            # 如果没有parent_id，设置为一级
            concept_data['level'] = 1
        
        # 创建概念
        concept = StockConcept(**concept_data)
        db.add(concept)
        db.flush()  # 获取id
        
        # 计算path
        if parent_id:
            parent = db.query(StockConcept).filter(
                StockConcept.id == parent_id
            ).first()
            concept.path = f"{parent.path}/{concept.id}"
        else:
            concept.path = str(concept.id)
        
        db.commit()
        db.refresh(concept)
        return concept
    
    @staticmethod
    def update(db: Session, concept_id: int, update_data: dict) -> Optional[StockConcept]:
        """更新概念板块（如果修改了parent_id，需要更新path和所有子概念的path）"""
        # 处理空字符串：将空字符串转换为 None，避免违反唯一约束
        if 'code' in update_data and update_data['code'] == '':
            update_data['code'] = None
        if 'description' in update_data and update_data['description'] == '':
            update_data['description'] = None
        
        concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
        if not concept:
            return None
        
        old_parent_id = concept.parent_id
        old_path = concept.path
        
        # 如果修改了parent_id
        if 'parent_id' in update_data and update_data['parent_id'] != old_parent_id:
            new_parent_id = update_data['parent_id']
            
            # 验证新父概念存在
            if new_parent_id:
                new_parent = db.query(StockConcept).filter(
                    StockConcept.id == new_parent_id
                ).first()
                if not new_parent:
                    raise ValueError("父概念不存在")
                # 更新level
                update_data['level'] = new_parent.level + 1
                if update_data['level'] > 3:
                    raise ValueError("层级不能超过3级")
            else:
                update_data['level'] = 1
            
            # 更新path
            if new_parent_id:
                new_parent = db.query(StockConcept).filter(
                    StockConcept.id == new_parent_id
                ).first()
                new_path = f"{new_parent.path}/{concept.id}"
            else:
                new_path = str(concept.id)
            
            update_data['path'] = new_path
            
            # 更新所有子概念的path
            StockConceptService._update_children_path(db, old_path, new_path)
        
        # 更新其他字段
        for key, value in update_data.items():
            if value is not None:
                setattr(concept, key, value)
        
        db.commit()
        db.refresh(concept)
        return concept
    
    @staticmethod
    def _update_children_path(db: Session, old_path: str, new_path: str):
        """递归更新所有子概念的path"""
        # 查询所有子概念（path以old_path开头）
        children = db.query(StockConcept).filter(
            StockConcept.path.like(f"{old_path}/%")
        ).all()
        
        for child in children:
            # 替换path前缀
            if child.path.startswith(old_path):
                child.path = child.path.replace(old_path, new_path, 1)
                db.add(child)
        
        db.commit()
    
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
