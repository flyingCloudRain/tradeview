"""
将股票概念关联到涨停池记录

使用方法:
    python scripts/link_concepts_to_zt_pool.py --date 2026-01-09
"""
import argparse
import sys
from pathlib import Path
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.zt_pool import ZtPool, ZtPoolDown
from app.services.stock_concept_service import StockConceptService


def update_zt_pool_concepts(target_date: date, update_text_field: bool = False):
    """
    更新涨停池记录的概念关联
    
    Args:
        target_date: 目标日期
        update_text_field: 是否同时更新 zt_pool.concept 文本字段（兼容旧数据）
    """
    db = SessionLocal()
    try:
        # 查询指定日期的涨停池记录
        zt_pool_items = db.query(ZtPool).filter(ZtPool.date == target_date).all()
        
        if not zt_pool_items:
            print(f"警告: {target_date} 没有涨停池数据")
            return
        
        print(f"找到 {len(zt_pool_items)} 条涨停池记录")
        
        updated_count = 0
        concept_text_updated = 0
        
        for item in zt_pool_items:
            # 获取股票的概念板块
            concepts = StockConceptService.get_by_stock_name(db, item.stock_name)
            
            if concepts:
                # 更新概念文本字段（可选，用于兼容）
                if update_text_field:
                    concept_names = [c.name for c in concepts]
                    new_concept_text = ', '.join(concept_names)
                    
                    # 如果原字段为空或不同，则更新
                    if not item.concept or item.concept != new_concept_text:
                        item.concept = new_concept_text
                        concept_text_updated += 1
                
                updated_count += 1
                concept_names_str = ', '.join([c.name for c in concepts])
                print(f"  {item.stock_name}: {len(concepts)} 个概念 - {concept_names_str}")
            else:
                print(f"  {item.stock_name}: 无概念板块关联")
        
        # 提交更改
        if update_text_field and concept_text_updated > 0:
            db.commit()
            print(f"\n已更新 {concept_text_updated} 条记录的概念文本字段")
        
        print(f"\n总计: {updated_count}/{len(zt_pool_items)} 条记录有概念板块关联")
        
    except Exception as e:
        print(f"错误: 处理失败 - {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def update_zt_pool_down_concepts(target_date: date, update_text_field: bool = False):
    """
    更新跌停池记录的概念关联
    
    Args:
        target_date: 目标日期
        update_text_field: 是否同时更新 zt_pool_down.concept 文本字段
    """
    db = SessionLocal()
    try:
        # 查询指定日期的跌停池记录
        zt_pool_down_items = db.query(ZtPoolDown).filter(ZtPoolDown.date == target_date).all()
        
        if not zt_pool_down_items:
            print(f"警告: {target_date} 没有跌停池数据")
            return
        
        print(f"找到 {len(zt_pool_down_items)} 条跌停池记录")
        
        updated_count = 0
        concept_text_updated = 0
        
        for item in zt_pool_down_items:
            # 获取股票的概念板块
            concepts = StockConceptService.get_by_stock_name(db, item.stock_name)
            
            if concepts:
                # 更新概念文本字段（可选，用于兼容）
                if update_text_field:
                    concept_names = [c.name for c in concepts]
                    new_concept_text = ', '.join(concept_names)
                    
                    # 如果原字段为空或不同，则更新
                    if not item.concept or item.concept != new_concept_text:
                        item.concept = new_concept_text
                        concept_text_updated += 1
                
                updated_count += 1
                concept_names_str = ', '.join([c.name for c in concepts])
                print(f"  {item.stock_name}: {len(concepts)} 个概念 - {concept_names_str}")
            else:
                print(f"  {item.stock_name}: 无概念板块关联")
        
        # 提交更改
        if update_text_field and concept_text_updated > 0:
            db.commit()
            print(f"\n已更新 {concept_text_updated} 条记录的概念文本字段")
        
        print(f"\n总计: {updated_count}/{len(zt_pool_down_items)} 条记录有概念板块关联")
        
    except Exception as e:
        print(f"错误: 处理失败 - {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='将股票概念关联到涨停池记录')
    parser.add_argument('--date', type=str, required=True, help='日期，格式：YYYY-MM-DD')
    parser.add_argument('--update-text', action='store_true', help='同时更新 concept 文本字段（兼容旧数据）')
    parser.add_argument('--include-down', action='store_true', help='同时处理跌停池')
    
    args = parser.parse_args()
    
    # 解析日期
    try:
        target_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"错误: 日期格式错误，应为 YYYY-MM-DD，实际: {args.date}")
        return
    
    print(f"正在处理 {target_date} 的涨停池数据...")
    print("="*60)
    
    # 处理涨停池
    update_zt_pool_concepts(target_date, args.update_text)
    
    # 处理跌停池（如果指定）
    if args.include_down:
        print("\n" + "="*60)
        print(f"正在处理 {target_date} 的跌停池数据...")
        print("="*60)
        update_zt_pool_down_concepts(target_date, args.update_text)


if __name__ == '__main__':
    main()
