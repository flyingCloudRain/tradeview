"""
将蓝箭航天的父概念更新为航天IPO
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
    lanjian = StockConceptService.get_by_name(db, '蓝箭航天')
    if not lanjian:
        print("❌ 未找到'蓝箭航天'概念")
        exit(1)
    
    # 查找航天IPO
    aerospace_ipo = StockConceptService.get_by_name(db, '航天IPO')
    if not aerospace_ipo:
        print("❌ 未找到'航天IPO'概念")
        exit(1)
    
    print(f"当前状态:")
    print(f"  蓝箭航天 - ID: {lanjian.id}, Level: {lanjian.level}, Parent ID: {lanjian.parent_id}")
    print(f"  航天IPO - ID: {aerospace_ipo.id}, Level: {aerospace_ipo.level}")
    
    if lanjian.parent_id == aerospace_ipo.id:
        print("\n✅ 蓝箭航天已经是航天IPO的子级概念")
    else:
        # 更新父概念
        update_data = {
            'parent_id': aerospace_ipo.id
        }
        updated = StockConceptService.update(db, lanjian.id, update_data)
        if updated:
            print(f"\n✅ 成功将蓝箭航天的父概念更新为航天IPO")
            print(f"   更新后 - ID: {updated.id}, Level: {updated.level}, Parent ID: {updated.parent_id}")
        else:
            print("\n❌ 更新失败")
            
except Exception as e:
    print(f"❌ 操作失败: {str(e)}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
