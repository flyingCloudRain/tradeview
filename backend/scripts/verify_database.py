"""
验证数据库表是否创建成功
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import inspect, text
from app.database.session import SessionLocal, engine


def verify_database():
    """验证数据库表"""
    print("=" * 50)
    print("数据库验证")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # 检查连接
        db.execute(text("SELECT 1"))
        print("✅ 数据库连接成功")
        
        # 获取所有表
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 已创建的表 ({len(tables)} 个):")
        expected_tables = [
            "lhb_detail",
            "lhb_institution",
            "capital_detail",
            "index_history",
            "sector_history",
            "stock_fund_flow",
            "zt_pool",
        ]
        
        for table in expected_tables:
            if table in tables:
                # 获取表信息
                columns = inspector.get_columns(table)
                print(f"  ✅ {table} ({len(columns)} 列)")
            else:
                print(f"  ❌ {table} - 未找到")
        
        # 检查索引
        print(f"\n📑 索引信息:")
        for table in expected_tables:
            if table in tables:
                indexes = inspector.get_indexes(table)
                if indexes:
                    print(f"  {table}:")
                    for idx in indexes:
                        print(f"    - {idx['name']}: {', '.join(idx['column_names'])}")
        
        # 检查外键
        print(f"\n🔗 外键关系:")
        for table in expected_tables:
            if table in tables:
                foreign_keys = inspector.get_foreign_keys(table)
                if foreign_keys:
                    print(f"  {table}:")
                    for fk in foreign_keys:
                        print(f"    - {fk['name']}: {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
        
        print("\n" + "=" * 50)
        print("✅ 数据库验证完成")
        
    except Exception as e:
        print(f"❌ 数据库验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    success = verify_database()
    sys.exit(0 if success else 1)

