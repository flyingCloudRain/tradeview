"""
为"航天IPO"概念添加子级概念
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.stock_concept_service import StockConceptService


def add_aerospace_ipo_subconcepts():
    """为航天IPO概念添加子级概念"""
    db = SessionLocal()
    try:
        # 查找"航天IPO"概念
        aerospace_ipo_concept = StockConceptService.get_by_name(db, "航天IPO")
        
        if not aerospace_ipo_concept:
            print("❌ 未找到'航天IPO'概念，请先创建'航天IPO'概念")
            return
        
        print(f"✅ 找到'航天IPO'概念 (ID: {aerospace_ipo_concept.id}, Level: {aerospace_ipo_concept.level})")
        
        # 检查是否可以添加子级（必须是1级或2级）
        if aerospace_ipo_concept.level >= 3:
            print(f"❌ '航天IPO'概念是{aerospace_ipo_concept.level}级概念，不能添加子级")
            return
        
        # 定义要添加的子级概念
        subconcepts = [
            {"name": "蓝箭航天", "code": None, "description": None, "sort_order": 1},
            {"name": "天兵科技", "code": None, "description": None, "sort_order": 2},
            {"name": "星河动力", "code": None, "description": None, "sort_order": 3},
            {"name": "星际荣耀", "code": None, "description": None, "sort_order": 4},
            {"name": "中科宇航", "code": None, "description": None, "sort_order": 5},
            {"name": "国星宇航", "code": None, "description": None, "sort_order": 6},
            {"name": "爱思达航天", "code": None, "description": None, "sort_order": 7},
            {"name": "微纳星空", "code": None, "description": None, "sort_order": 8},
        ]
        
        created_count = 0
        existing_count = 0
        
        for subconcept_data in subconcepts:
            # 检查是否已存在
            existing = StockConceptService.get_by_name(db, subconcept_data["name"])
            if existing:
                print(f"⚠️  概念已存在: {subconcept_data['name']} (ID: {existing.id})")
                existing_count += 1
            else:
                # 设置父概念ID
                subconcept_data["parent_id"] = aerospace_ipo_concept.id
                
                # 创建子级概念
                concept = StockConceptService.create(db, subconcept_data)
                print(f"✅ 创建子级概念: {subconcept_data['name']} (ID: {concept.id}, Level: {concept.level})")
                created_count += 1
        
        print(f"\n📊 完成统计:")
        print(f"   - 新创建: {created_count} 个")
        print(f"   - 已存在: {existing_count} 个")
        print(f"   - 总计: {len(subconcepts)} 个")
        
    except Exception as e:
        print(f"❌ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    add_aerospace_ipo_subconcepts()
