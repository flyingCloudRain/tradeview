"""
清除交易日历数据库中的所有数据

执行方式：
    poetry run python backend/scripts/clear_trading_calendar.py
或：
    python backend/scripts/clear_trading_calendar.py

警告：此脚本将删除交易日历表中的所有数据，操作不可逆！
"""
import sys
from pathlib import Path
from sqlalchemy import func

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.trading_calendar import TradingCalendar


def clear_trading_calendar(session, confirm: bool = False) -> int:
    """
    清除交易日历表中的所有数据
    
    Args:
        session: 数据库会话
        confirm: 是否已确认删除操作
    
    Returns:
        删除的记录数
    """
    # 先统计记录数
    total_count = session.query(func.count(TradingCalendar.id)).scalar()
    
    if total_count == 0:
        print("✅ 交易日历表为空，无需清除")
        return 0
    
    if not confirm:
        print(f"⚠️  警告：此操作将删除交易日历表中的所有 {total_count} 条记录！")
        print("⚠️  此操作不可逆，请谨慎操作！")
        response = input("请输入 'YES' 确认删除，或按 Enter 取消: ").strip()
        
        if response != 'YES':
            print("❌ 操作已取消")
            return 0
    
    # 删除所有记录
    deleted_count = session.query(TradingCalendar).delete()
    session.commit()
    
    print(f"✅ 成功删除 {deleted_count} 条交易日历记录")
    return deleted_count


def main():
    """主函数"""
    session = SessionLocal()
    try:
        # 检查是否需要确认（可以通过命令行参数跳过确认）
        confirm = '--yes' in sys.argv or '-y' in sys.argv
        
        deleted_count = clear_trading_calendar(session, confirm=confirm)
        
        if deleted_count > 0:
            print("=== 清除完成 ===")
            print(f"已删除 {deleted_count} 条交易日历记录")
    except Exception as e:
        session.rollback()
        print(f"❌ 清除失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
