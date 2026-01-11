"""
初始化常见股票概念板块
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.stock_concept import StockConcept
from app.services.stock_concept_service import StockConceptService


COMMON_CONCEPTS = [
    {"name": "人工智能", "code": "AI"},
    {"name": "新能源", "code": "NE"},
    {"name": "5G", "code": "5G"},
    {"name": "芯片", "code": "CHIP"},
    {"name": "新能源汽车", "code": "NEV"},
    {"name": "光伏", "code": "PV"},
    {"name": "锂电池", "code": "BATTERY"},
    {"name": "医药", "code": "MED"},
    {"name": "消费电子", "code": "CE"},
    {"name": "军工", "code": "DEFENSE"},
]


def init_concepts():
    """初始化常见概念板块"""
    db = SessionLocal()
    try:
        count = 0
        for concept_data in COMMON_CONCEPTS:
            # 检查是否已存在
            existing = StockConceptService.get_by_name(db, concept_data["name"])
            if not existing:
                StockConceptService.create(db, concept_data)
                count += 1
                print(f"创建概念板块: {concept_data['name']}")
            else:
                print(f"概念板块已存在: {concept_data['name']}")
        
        print(f"\n初始化完成，共创建 {count} 个概念板块")
    except Exception as e:
        print(f"初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_concepts()
