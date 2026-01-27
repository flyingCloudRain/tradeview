"""
为"卫星"概念添加子级概念
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.stock_concept_service import StockConceptService


def add_satellite_subconcepts():
    """为卫星概念添加子级概念"""
    db = SessionLocal()
    try:
        # 查找"卫星"概念
        satellite_concept = StockConceptService.get_by_name(db, "卫星")
        
        if not satellite_concept:
            print("❌ 未找到'卫星'概念，请先创建'卫星'概念")
            return
        
        print(f"✅ 找到'卫星'概念 (ID: {satellite_concept.id}, Level: {satellite_concept.level})")
        
        # 检查是否可以添加子级（必须是1级或2级）
        if satellite_concept.level >= 3:
            print(f"❌ '卫星'概念是{satellite_concept.level}级概念，不能添加子级")
            return
        
        # 定义要添加的子级概念
        subconcepts = [
            {"name": "卫星导航", "code": None, "description": None, "sort_order": 1},
            {"name": "卫星遥感", "code": None, "description": None, "sort_order": 2},
            {"name": "卫星测控", "code": None, "description": None, "sort_order": 3},
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
                subconcept_data["parent_id"] = satellite_concept.id
                
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
    add_satellite_subconcepts()
