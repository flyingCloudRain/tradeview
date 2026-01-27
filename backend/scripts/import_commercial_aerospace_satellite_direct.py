"""
直接导入：商业航天 -> 卫星 -> 千帆星座 -> 个股

数据：
    商业航天	卫星	千帆星座	乾照光电、东方明珠、天银机电、上海瀚讯、航天智装、立昂微、陕西华达、长江通信、北摩高科、隆盛科技、鸿远电子

使用方法:
    python scripts/import_commercial_aerospace_satellite_direct.py
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.stock_concept_service import StockConceptService, StockConceptMappingService


def import_commercial_aerospace_satellite():
    """导入商业航天 -> 卫星 -> 千帆星座 -> 个股"""
    db = SessionLocal()
    try:
        print("=" * 60)
        print("导入：商业航天 -> 卫星 -> 千帆星座 -> 个股")
        print("=" * 60)
        
        # 步骤1：创建概念层级
        print("\n📋 步骤1：创建概念层级结构")
        
        # 1.1 一级概念：商业航天
        level1_concept, is_new1 = get_or_create_concept(db, "商业航天", None, 0)
        if is_new1:
            print(f"  ✅ 创建一级概念: 商业航天 (ID: {level1_concept.id})")
        else:
            print(f"  ⚠️  一级概念已存在: 商业航天 (ID: {level1_concept.id})")
        
        # 1.2 二级概念：卫星
        level2_concept, is_new2 = get_or_create_concept(db, "卫星", level1_concept.id, 0)
        if is_new2:
            print(f"  ✅ 创建二级概念: 卫星 (ID: {level2_concept.id})")
        else:
            print(f"  ⚠️  二级概念已存在: 卫星 (ID: {level2_concept.id})")
        
        # 1.3 三级概念：千帆星座
        level3_concept, is_new3 = get_or_create_concept(db, "千帆星座", level2_concept.id, 0)
        if is_new3:
            print(f"  ✅ 创建三级概念: 千帆星座 (ID: {level3_concept.id})")
        else:
            print(f"  ⚠️  三级概念已存在: 千帆星座 (ID: {level3_concept.id})")
        
        # 步骤2：关联个股
        print("\n📋 步骤2：关联个股到'千帆星座'概念")
        
        stock_names = [
            '乾照光电',
            '东方明珠',
            '天银机电',
            '上海瀚讯',
            '航天智装',
            '立昂微',
            '陕西华达',
            '长江通信',
            '北摩高科',
            '隆盛科技',
            '鸿远电子'
        ]
        
        inserted_count = 0
        existing_count = 0
        
        for stock_name in stock_names:
            try:
                StockConceptMappingService.add_concept_to_stock(
                    db, stock_name, level3_concept.id
                )
                print(f"  ✅ 关联个股: {stock_name}")
                inserted_count += 1
            except Exception as e:
                # 检查是否是因为已存在
                from app.models.stock_concept import StockConceptMapping
                existing = db.query(StockConceptMapping).filter(
                    StockConceptMapping.stock_name == stock_name,
                    StockConceptMapping.concept_id == level3_concept.id
                ).first()
                if existing:
                    print(f"  ⚠️  已存在: {stock_name}")
                    existing_count += 1
                else:
                    print(f"  ❌ 关联失败: {stock_name} - {e}")
        
        # 步骤3：更新stock_count
        print("\n📋 步骤3：更新stock_count统计字段")
        from app.models.stock_concept import StockConcept, StockConceptMapping
        concepts = db.query(StockConcept).all()
        for concept in concepts:
            count = db.query(StockConceptMapping).filter(
                StockConceptMapping.concept_id == concept.id
            ).count()
            concept.stock_count = count
        
        db.commit()
        
        # 打印统计信息
        print("\n" + "=" * 60)
        print("📊 导入统计:")
        print(f"  概念创建 - 一级: {'新建' if is_new1 else '已存在'}, 二级: {'新建' if is_new2 else '已存在'}, 三级: {'新建' if is_new3 else '已存在'}")
        print(f"  个股关联 - 新增: {inserted_count}, 已存在: {existing_count}, 总计: {len(stock_names)}")
        print("=" * 60)
        
        # 验证查询
        print("\n📋 验证查询结果:")
        final_count = db.query(StockConceptMapping).filter(
            StockConceptMapping.concept_id == level3_concept.id
        ).count()
        print(f"  '千帆星座'概念关联个股数: {final_count}")
        
        stocks = db.query(StockConceptMapping.stock_name).filter(
            StockConceptMapping.concept_id == level3_concept.id
        ).all()
        stock_list = [s[0] for s in stocks]
        print(f"  个股列表: {', '.join(sorted(stock_list))}")
        
        print("\n✅ 导入完成！")
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()
    
    return 0


def get_or_create_concept(db, concept_name: str, parent_id, sort_order: int = 0):
    """获取或创建概念"""
    from app.services.stock_concept_service import StockConceptService
    
    concept = StockConceptService.get_by_name(db, concept_name)
    if concept:
        # 如果指定了parent_id，检查是否需要更新
        if parent_id and concept.parent_id != parent_id:
            update_data = {'parent_id': parent_id}
            concept = StockConceptService.update(db, concept.id, update_data)
        return concept, False
    
    # 创建新概念
    concept_data = {
        "name": concept_name,
        "parent_id": parent_id,
        "sort_order": sort_order
    }
    concept = StockConceptService.create(db, concept_data)
    return concept, True


if __name__ == '__main__':
    sys.exit(import_commercial_aerospace_satellite())
