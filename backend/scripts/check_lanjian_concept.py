"""
检查蓝箭航天的父概念
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.stock_concept_service import StockConceptService

db = SessionLocal()
try:
    # 查找蓝箭航天
    concept = StockConceptService.get_by_name(db, '蓝箭航天')
    if concept:
        print(f'蓝箭航天 - ID: {concept.id}, Level: {concept.level}, Parent ID: {concept.parent_id}')
        if concept.parent_id:
            parent = StockConceptService.get_by_id(db, concept.parent_id)
            if parent:
                print(f'父概念: {parent.name} (ID: {parent.id})')
        else:
            print('父概念: 无')
    
    # 查找航天IPO
    aerospace_ipo = StockConceptService.get_by_name(db, '航天IPO')
    if aerospace_ipo:
        print(f'\n航天IPO - ID: {aerospace_ipo.id}, Level: {aerospace_ipo.level}')
finally:
    db.close()
