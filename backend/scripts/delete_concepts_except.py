#!/usr/bin/env python3
"""
删除除指定概念外的所有概念题材
保留：商业航天、AI
"""
import sys
import os
import argparse

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.models.stock_concept import StockConcept, StockConceptMapping
from app.services.stock_concept_service import StockConceptService


def delete_concepts_except(db: Session, keep_names: list[str], auto_confirm: bool = False):
    """
    删除除指定名称外的所有概念
    
    Args:
        db: 数据库会话
        keep_names: 要保留的概念名称列表（支持模糊匹配）
    """
    # 查询所有概念
    all_concepts = db.query(StockConcept).all()
    
    # 找到要保留的概念ID
    keep_ids = set()
    keep_concepts = []
    
    for concept in all_concepts:
        for keep_name in keep_names:
            if keep_name.lower() in concept.name.lower() or concept.name.lower() in keep_name.lower():
                keep_ids.add(concept.id)
                keep_concepts.append(concept)
                print(f"✅ 保留概念: {concept.name} (ID: {concept.id}, Level: {concept.level})")
                break
    
    if not keep_ids:
        print(f"⚠️  警告: 未找到要保留的概念: {keep_names}")
        if not auto_confirm:
            response = input("是否继续删除所有概念？(yes/no): ")
            if response.lower() != 'yes':
                print("操作已取消")
                return
        else:
            print("⚠️  自动确认模式：将删除所有概念")
    
    # 找到要删除的概念
    concepts_to_delete = [c for c in all_concepts if c.id not in keep_ids]
    
    print(f"\n📊 统计信息:")
    print(f"   总概念数: {len(all_concepts)}")
    print(f"   保留概念数: {len(keep_ids)}")
    print(f"   待删除概念数: {len(concepts_to_delete)}")
    
    if not concepts_to_delete:
        print("\n✅ 没有需要删除的概念")
        return
    
    # 显示要删除的概念列表
    print(f"\n🗑️  待删除的概念列表:")
    for concept in concepts_to_delete:
        print(f"   - {concept.name} (ID: {concept.id}, Level: {concept.level})")
    
    # 确认删除
    print(f"\n⚠️  警告: 即将删除 {len(concepts_to_delete)} 个概念")
    if not auto_confirm:
        response = input("确认删除？(yes/no): ")
        if response.lower() != 'yes':
            print("操作已取消")
            return
    else:
        print("✅ 自动确认模式：开始删除...")
    
    # 删除概念（需要先删除子概念，或者使用级联删除）
    # 按层级从高到低删除（先删除三级，再删除二级，最后删除一级）
    deleted_count = 0
    
    # 先删除所有三级概念
    level3_to_delete = [c for c in concepts_to_delete if c.level == 3]
    for concept in level3_to_delete:
        try:
            db.delete(concept)
            deleted_count += 1
            print(f"   删除: {concept.name} (ID: {concept.id}, Level: 3)")
        except Exception as e:
            print(f"   ❌ 删除失败: {concept.name} - {str(e)}")
    
    # 再删除所有二级概念
    level2_to_delete = [c for c in concepts_to_delete if c.level == 2]
    for concept in level2_to_delete:
        try:
            db.delete(concept)
            deleted_count += 1
            print(f"   删除: {concept.name} (ID: {concept.id}, Level: 2)")
        except Exception as e:
            print(f"   ❌ 删除失败: {concept.name} - {str(e)}")
    
    # 最后删除所有一级概念
    level1_to_delete = [c for c in concepts_to_delete if c.level == 1]
    for concept in level1_to_delete:
        try:
            db.delete(concept)
            deleted_count += 1
            print(f"   删除: {concept.name} (ID: {concept.id}, Level: 1)")
        except Exception as e:
            print(f"   ❌ 删除失败: {concept.name} - {str(e)}")
    
    # 提交事务
    try:
        db.commit()
        print(f"\n✅ 成功删除 {deleted_count} 个概念")
        
        # 显示保留的概念
        remaining_concepts = db.query(StockConcept).all()
        print(f"\n📋 保留的概念列表:")
        for concept in remaining_concepts:
            print(f"   - {concept.name} (ID: {concept.id}, Level: {concept.level})")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 删除失败: {str(e)}")
        raise


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='删除除指定概念外的所有概念题材')
    parser.add_argument('--yes', '-y', action='store_true', help='自动确认，跳过交互式确认')
    args = parser.parse_args()
    
    print("=" * 60)
    print("删除概念题材（保留：商业航天、AI）")
    print("=" * 60)
    print()
    
    # 要保留的概念名称（支持模糊匹配）
    keep_names = ["商业航天", "AI"]
    
    db = SessionLocal()
    try:
        delete_concepts_except(db, keep_names, auto_confirm=args.yes)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
