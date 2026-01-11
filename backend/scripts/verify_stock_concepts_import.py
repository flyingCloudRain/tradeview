"""
验证股票概念数据导入结果

使用方法:
    python scripts/verify_stock_concepts_import.py --stock 鲁信创投
    python scripts/verify_stock_concepts_import.py --concept AI
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.stock_concept_service import StockConceptService, StockConceptMappingService


def verify_stock(stock_name: str):
    """验证股票的概念板块"""
    db = SessionLocal()
    try:
        concepts = StockConceptService.get_by_stock_name(db, stock_name)
        print(f"\n股票: {stock_name}")
        print(f"概念板块数量: {len(concepts)}")
        if concepts:
            print("概念列表:")
            for concept in concepts:
                print(f"  - {concept.name} (ID: {concept.id})")
        else:
            print("  无概念板块")
    finally:
        db.close()


def verify_concept(concept_name: str):
    """验证概念板块关联的股票"""
    db = SessionLocal()
    try:
        concept = StockConceptService.get_by_name(db, concept_name)
        if not concept:
            print(f"\n概念板块 '{concept_name}' 不存在")
            return
        
        # 查询关联的股票
        from app.models.stock_concept import StockConceptMapping
        mappings = db.query(StockConceptMapping).filter(
            StockConceptMapping.concept_id == concept.id
        ).all()
        
        print(f"\n概念板块: {concept_name} (ID: {concept.id})")
        print(f"关联股票数量: {len(mappings)}")
        if mappings:
            print("股票列表:")
            for mapping in mappings[:20]:  # 只显示前20个
                print(f"  - {mapping.stock_name}")
            if len(mappings) > 20:
                print(f"  ... 还有 {len(mappings) - 20} 个股票")
    finally:
        db.close()


def show_statistics():
    """显示统计信息"""
    db = SessionLocal()
    try:
        from app.models.stock_concept import StockConcept, StockConceptMapping
        from sqlalchemy import func
        
        # 统计概念板块总数
        total_concepts = db.query(StockConcept).count()
        total_mappings = db.query(StockConceptMapping).count()
        
        # 统计有概念的股票数量
        unique_stocks = db.query(func.count(func.distinct(StockConceptMapping.stock_name))).scalar()
        
        print("\n" + "="*50)
        print("数据统计:")
        print(f"  概念板块总数: {total_concepts}")
        print(f"  股票概念关联总数: {total_mappings}")
        print(f"  有概念的股票数量: {unique_stocks}")
        print("="*50)
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='验证股票概念数据导入结果')
    parser.add_argument('--stock', type=str, help='股票名称')
    parser.add_argument('--concept', type=str, help='概念板块名称')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    if args.stock:
        verify_stock(args.stock)
    elif args.concept:
        verify_concept(args.concept)
    elif args.stats:
        show_statistics()
    else:
        # 默认显示统计信息
        show_statistics()
        print("\n提示: 使用 --stock <股票名> 查看股票的概念板块")
        print("      使用 --concept <概念名> 查看概念板块关联的股票")


if __name__ == '__main__':
    main()
