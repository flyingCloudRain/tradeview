"""
批量导入交易日历数据
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
from app.database.session import SessionLocal
from app.services.trading_calendar_service import TradingCalendarService


def import_trading_calendar_data():
    """导入交易日历数据"""
    db = SessionLocal()
    
    try:
        # 定义要导入的数据
        # 格式: (日期, 股票名称, 操作方向, 策略, 来源)
        data = [
            # 2026-01-09 排板策略
            ("2026-01-09", "美年健康", "买入", "排板", None),
            ("2026-01-09", "东湖高新", "买入", "排板", None),
            ("2026-01-09", "辉煌科技", "买入", "排板", None),
            ("2026-01-09", "蓝思科技", "买入", "排板", None),
            
            # 2026-01-05 低吸策略
            ("2026-01-05", "北斗星通", "买入", "低吸", None),
            ("2026-01-05", "上海翰讯", "买入", "低吸", None),
            ("2026-01-05", "陕西华达", "买入", "低吸", None),
            ("2026-01-05", "久之洋", "买入", "低吸", None),
            
            # 2026-01-06 低吸策略
            ("2026-01-06", "立昂微", "买入", "低吸", None),
            
            # 2026-01-08 排板策略
            ("2026-01-08", "东方明珠", "买入", "排板", None),
            ("2026-01-08", "百利电气", "买入", "排板", None),
        ]
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for date_str, stock_name, direction, strategy, source in data:
            try:
                # 解析日期
                date_obj = date.fromisoformat(date_str)
                
                # 检查是否已存在相同的记录（同日期、同股票、同方向、同策略）
                from app.models.trading_calendar import TradingCalendar
                existing = db.query(TradingCalendar).filter(
                    TradingCalendar.date == date_obj,
                    TradingCalendar.stock_name == stock_name,
                    TradingCalendar.direction == direction,
                    TradingCalendar.strategy == strategy
                ).first()
                
                if existing:
                    print(f"⏭️  跳过已存在记录: {date_str} {stock_name} {direction} {strategy}")
                    skip_count += 1
                    continue
                
                # 创建新记录
                calendar_data = {
                    "date": date_obj,
                    "stock_name": stock_name,
                    "direction": direction,
                    "strategy": strategy,
                    "source": source,
                }
                
                TradingCalendarService.create(db, calendar_data)
                print(f"✅ 成功导入: {date_str} {stock_name} {direction} {strategy}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 导入失败: {date_str} {stock_name} - {str(e)}")
                error_count += 1
                continue
        
        print(f"\n📊 导入完成:")
        print(f"   ✅ 成功: {success_count} 条")
        print(f"   ⏭️  跳过: {skip_count} 条")
        print(f"   ❌ 失败: {error_count} 条")
        
    except Exception as e:
        print(f"❌ 导入过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    import_trading_calendar_data()
