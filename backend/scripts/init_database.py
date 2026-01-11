"""
数据库初始化脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.base import Base
from app.database.session import engine
from app.models import *  # 导入所有模型


def init_database():
    """初始化数据库，创建所有表"""
    print("开始创建数据库表...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功！")
        
        # 显示创建的表
        print("\n已创建的表：")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
        raise


if __name__ == "__main__":
    init_database()

