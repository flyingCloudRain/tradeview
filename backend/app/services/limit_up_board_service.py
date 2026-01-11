"""
涨停板分析服务
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc, func, or_, cast, String
from typing import Optional, List, Tuple
from datetime import date, time
import math
import json

from app.models.limit_up_board import LimitUpBoard, LimitUpBoardConcept
from app.models.stock_concept import StockConcept
from app.schemas.limit_up_board import LimitUpBoardCreate, LimitUpBoardUpdate
from app.services.stock_concept_service import StockConceptService


class LimitUpBoardService:
    """涨停板分析服务类"""
    
    @staticmethod
    def extract_concepts_from_keywords(
        db: Session,
        keywords: Optional[str],
        provided_concept_names: Optional[List[str]] = None
    ) -> List[int]:
        """
        从关键字中提取概念板块ID列表
        返回: 概念板块ID列表
        """
        concept_ids = []
        
        if not keywords and not provided_concept_names:
            return concept_ids
        
        # 获取所有概念板块名称（用于匹配）
        all_concepts, _ = StockConceptService.get_list(db, page=1, page_size=10000)
        concept_name_map = {concept.name: concept.id for concept in all_concepts}
        
        # 如果提供了概念名称，直接使用
        if provided_concept_names:
            for name in provided_concept_names:
                if name in concept_name_map:
                    concept_ids.append(concept_name_map[name])
        
        # 从关键字中提取概念板块
        if keywords:
            keywords_lower = keywords.lower()
            for concept_name, concept_id in concept_name_map.items():
                # 检查概念名称是否在关键字中出现
                if concept_name.lower() in keywords_lower:
                    if concept_id not in concept_ids:
                        concept_ids.append(concept_id)
        
        return concept_ids
    
    @staticmethod
    def get_list(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        target_date: Optional[date] = None,
        board_name: Optional[str] = None,
        stock_code: Optional[str] = None,
        stock_name: Optional[str] = None,
        tag: Optional[str] = None,
        limit_up_reason: Optional[str] = None,
        concept_id: Optional[int] = None,
        concept_name: Optional[str] = None,
    ) -> Tuple[List[LimitUpBoard], int]:
        """
        获取涨停板分析列表
        """
        query = db.query(LimitUpBoard)
        
        if target_date:
            query = query.filter(LimitUpBoard.date == target_date)
        
        if board_name:
            query = query.filter(LimitUpBoard.board_name == board_name)
        
        if stock_code:
            query = query.filter(LimitUpBoard.stock_code == stock_code)
        
        if stock_name:
            query = query.filter(LimitUpBoard.stock_name.like(f"%{stock_name}%"))
        
        if limit_up_reason:
            query = query.filter(LimitUpBoard.limit_up_reason.like(f"%{limit_up_reason}%"))
        
        if tag:
            # 对于 JSON 字段，需要特殊处理
            query = query.filter(
                cast(LimitUpBoard.tags, String).like(f"%{tag}%")
            )
        
        # 概念板块筛选
        if concept_id or concept_name:
            query = query.join(LimitUpBoardConcept).join(StockConcept)
            if concept_id:
                query = query.filter(StockConcept.id == concept_id)
            if concept_name:
                query = query.filter(StockConcept.name.like(f"%{concept_name}%"))
        
        # 获取总数
        total = query.count()
        
        # 分页和排序
        query = query.order_by(desc(LimitUpBoard.date), LimitUpBoard.board_name, LimitUpBoard.stock_code)
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        items = query.all()
        
        # 加载概念板块关联
        for item in items:
            concept_mappings = db.query(LimitUpBoardConcept).filter(
                LimitUpBoardConcept.limit_up_board_id == item.id
            ).all()
            concepts = [mapping.concept for mapping in concept_mappings]
            item._concepts = concepts
        
        return items, total
    
    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[LimitUpBoard]:
        """根据ID获取涨停板分析"""
        item = db.query(LimitUpBoard).filter(LimitUpBoard.id == item_id).first()
        if item:
            # 加载概念板块关联
            concept_mappings = db.query(LimitUpBoardConcept).filter(
                LimitUpBoardConcept.limit_up_board_id == item.id
            ).all()
            concepts = [mapping.concept for mapping in concept_mappings]
            item._concepts = concepts
        return item
    
    @staticmethod
    def create(db: Session, item: LimitUpBoardCreate, auto_extract_concepts: bool = True) -> LimitUpBoard:
        """创建涨停板分析"""
        # 提取概念板块ID
        concept_ids = []
        if auto_extract_concepts:
            concept_ids = LimitUpBoardService.extract_concepts_from_keywords(
                db, item.keywords, item.concept_names
            )
        
        # 创建主记录
        db_item = LimitUpBoard(
            date=item.date,
            board_name=item.board_name,
            board_stock_count=item.board_stock_count,
            stock_code=item.stock_code,
            stock_name=item.stock_name,
            limit_up_days=item.limit_up_days,
            limit_up_time=item.limit_up_time,
            circulation_market_value=item.circulation_market_value,
            turnover_amount=item.turnover_amount,
            keywords=item.keywords,
            limit_up_reason=item.limit_up_reason,
            tags=item.tags,
        )
        db.add(db_item)
        db.flush()  # 获取ID
        
        # 创建概念板块关联
        for concept_id in concept_ids:
            mapping = LimitUpBoardConcept(
                limit_up_board_id=db_item.id,
                concept_id=concept_id
            )
            db.add(mapping)
        
        db.commit()
        db.refresh(db_item)
        
        # 加载概念板块
        concept_mappings = db.query(LimitUpBoardConcept).filter(
            LimitUpBoardConcept.limit_up_board_id == db_item.id
        ).all()
        concepts = [mapping.concept for mapping in concept_mappings]
        db_item._concepts = concepts
        
        return db_item
    
    @staticmethod
    def batch_create(db: Session, items: List[LimitUpBoardCreate], auto_extract_concepts: bool = True) -> List[LimitUpBoard]:
        """批量创建涨停板分析"""
        created_items = []
        
        for item in items:
            created_item = LimitUpBoardService.create(db, item, auto_extract_concepts)
            created_items.append(created_item)
        
        return created_items
    
    @staticmethod
    def update(db: Session, item_id: int, item_update: LimitUpBoardUpdate) -> Optional[LimitUpBoard]:
        """更新涨停板分析"""
        db_item = db.query(LimitUpBoard).filter(LimitUpBoard.id == item_id).first()
        if not db_item:
            return None
        
        update_data = item_update.model_dump(exclude_unset=True, exclude={'concept_names'})
        for key, value in update_data.items():
            setattr(db_item, key, value)
        
        # 更新概念板块关联
        if 'concept_names' in item_update.model_dump(exclude_unset=True):
            # 删除旧关联
            db.query(LimitUpBoardConcept).filter(
                LimitUpBoardConcept.limit_up_board_id == item_id
            ).delete()
            
            # 创建新关联
            concept_ids = LimitUpBoardService.extract_concepts_from_keywords(
                db, db_item.keywords, item_update.concept_names
            )
            for concept_id in concept_ids:
                mapping = LimitUpBoardConcept(
                    limit_up_board_id=item_id,
                    concept_id=concept_id
                )
                db.add(mapping)
        
        db.commit()
        db.refresh(db_item)
        
        # 加载概念板块
        concept_mappings = db.query(LimitUpBoardConcept).filter(
            LimitUpBoardConcept.limit_up_board_id == db_item.id
        ).all()
        concepts = [mapping.concept for mapping in concept_mappings]
        db_item._concepts = concepts
        
        return db_item
    
    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        """删除涨停板分析"""
        db_item = db.query(LimitUpBoard).filter(LimitUpBoard.id == item_id).first()
        if not db_item:
            return False
        
        db.delete(db_item)
        db.commit()
        return True
    
    @staticmethod
    def delete_by_date(db: Session, target_date: date) -> int:
        """根据日期删除涨停板分析"""
        deleted_count = db.query(LimitUpBoard).filter(LimitUpBoard.date == target_date).delete()
        db.commit()
        return deleted_count
    
    @staticmethod
    def get_board_statistics(
        db: Session,
        target_date: Optional[date] = None
    ) -> dict:
        """获取板块统计信息"""
        query = db.query(LimitUpBoard)
        
        if target_date:
            query = query.filter(LimitUpBoard.date == target_date)
        
        # 统计每个板块的股票数量
        board_stats = db.query(
            LimitUpBoard.board_name,
            func.count(LimitUpBoard.id).label('stock_count')
        ).group_by(LimitUpBoard.board_name)
        
        if target_date:
            board_stats = board_stats.filter(LimitUpBoard.date == target_date)
        
        board_stats = board_stats.order_by(desc('stock_count')).all()
        
        return {
            'board_distribution': [
                {'board_name': name, 'stock_count': count}
                for name, count in board_stats
            ],
            'total_boards': len(board_stats),
            'total_stocks': sum(count for _, count in board_stats)
        }
