"""
批量导入交易日历数据
"""
import sys
from pathlib import Path
import re
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import date
from app.database.session import SessionLocal
from app.services.trading_calendar_service import TradingCalendarService


def parse_chinese_date(date_str: str, reference_date: date = None) -> date:
    """
    解析中文日期格式
    支持格式：
    - "1月8日" -> 根据参考日期智能推断年份
    - "2025年12月22日" -> 2025-12-22
    - "2026-01-09" -> 2026-01-09 (ISO格式)
    
    Args:
        date_str: 日期字符串
        reference_date: 参考日期，用于推断简化格式的年份（默认为当前日期）
    """
    if not date_str or not date_str.strip():
        raise ValueError("日期字符串不能为空")
    
    date_str = date_str.strip()
    
    # 处理ISO格式 "2026-01-09"
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date.fromisoformat(date_str)
    
    # 处理完整格式 "2025年12月22日"
    match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
        return date(year, month, day)
    
    # 处理简化格式 "1月8日" (智能推断年份)
    match = re.match(r'(\d{1,2})月(\d{1,2})日', date_str)
    if match:
        month, day = int(match.group(1)), int(match.group(2))
        
        # 如果没有提供参考日期，使用当前日期
        if reference_date is None:
            reference_date = date.today()
        
        # 智能推断年份：
        # 根据参考日期和要解析的月份，智能推断年份
        ref_year = reference_date.year
        ref_month = reference_date.month
        
        # 计算月份差值（考虑跨年情况）
        month_diff = month - ref_month
        
        # 处理跨年情况
        if ref_month >= 10 and month <= 3:
            # 参考日期是10-12月，要解析1-3月，应该是下一年
            inferred_year = ref_year + 1
        elif ref_month <= 3 and month >= 10:
            # 参考日期是1-3月，要解析10-12月，应该是前一年
            inferred_year = ref_year - 1
        elif month_diff > 6:
            # 月份差值大于6个月，可能是下一年（不太可能，但处理边界情况）
            inferred_year = ref_year + 1
        elif month_diff < -6:
            # 月份差值小于-6个月，可能是前一年（不太可能，但处理边界情况）
            inferred_year = ref_year - 1
        else:
            # 其他情况，使用参考日期的年份
            inferred_year = ref_year
        
        return date(inferred_year, month, day)
    
    raise ValueError(f"无法解析日期格式: {date_str}")


def import_trading_calendar_data():
    """导入交易日历数据"""
    db = SessionLocal()
    
    try:
        # 定义要导入的数据
        # 格式: (日期字符串, 股票名称, 操作方向, 策略, 价格, 来源, 备注)
        # 日期格式支持中文格式，如 "1月8日" 或 "2025年12月22日"
        data = [
            # 2025年12月22日的数据
            ("2025年12月22日", "爱朋医疗", "买入", "排板", 42.63, "韩叔", None),
            ("2025年12月22日", "再升科技", "买入", "排板", 13.08, "韩叔", None),
            ("2025年12月22日", "航天动力", "买入", "排板", 43.34, "韩叔", None),
            ("2025年12月22日", "西部材料", "买入", "排板", 46.3, "韩叔", None),
            ("2025年12月22日", "金风科技", "买入", "排板", 37.25, "韩叔", None),
            ("2025年12月22日", "华菱线缆", "买入", "排板", 36.36, "韩叔", None),
            ("2025年12月22日", "通宇通信", "买入", "排板", 32.65, "韩叔", None),
            ("2025年12月22日", "浙江世宝", "买入", "排板", 19.42, "韩叔", None),
            ("2025年12月22日", "东百集团", "买入", "排板", 21.45, "韩叔", None),
            ("2025年12月22日", "海南发展", "买入", "排板", 43.27, "韩叔", None),
            ("2025年12月22日", "天际股份", "买入", "排板", 36.74, "韩叔", None),
            ("2025年12月22日", "泰尔股份", "买入", "排板", 21.88, "韩叔", None),
            ("2025年12月22日", "三花智控", "买入", "排板", 22.757, "韩叔", None),
            ("2025年12月22日", "天奇股份", "买入", "排板", 49.515, "韩叔", None),
            ("2025年12月22日", "万向钱潮", "买入", "排板", 24.52, "韩叔", None),
            
            # 2026年1月8日的数据
            ("2026年1月8日", "爱朋医疗", "买入", "低吸", 42.48, "韩叔", "回调低吸"),
            ("2026年1月8日", "再升科技", "买入", "低吸", 9.96, "韩叔", None),
            ("2026年1月8日", "航天动力", "买入", "低吸", 47.39, "韩叔", None),
            ("2026年1月8日", "西部材料", "买入", "低吸", 11.25, "韩叔", None),
            ("2026年1月8日", "金风科技", "买入", "低吸", 52.51, "韩叔", None),
            ("2026年1月8日", "华菱线缆", "买入", "低吸", 23.43, "韩叔", None),
            ("2026年1月8日", "通宇通信", "买入", "低吸", 17.26, "韩叔", None),
            ("2026年1月8日", "浙江世宝", "买入", "低吸", 17.02, "韩叔", None),
            ("2026年1月8日", "东百集团", "买入", "低吸", 23.99, "韩叔", None),
            ("2026年1月8日", "海南发展", "买入", "低吸", 22.44, "韩叔", None),
            ("2026年1月8日", "天际股份", "买入", "低吸", 22.21, "韩叔", None),
            ("2026年1月8日", "泰尔股份", "买入", "低吸", 24.0, "韩叔", None),
            ("2026年1月8日", "三花智控", "买入", "低吸", 25.21, "韩叔", None),
            ("2026年1月8日", "天奇股份", "买入", "低吸", 46.3, "韩叔", None),
            ("2026年1月8日", "万向钱潮", "卖出", None, None, "韩叔", "3连板"),
            
            # 2026年1月9日 排板策略
            ("2026年1月9日", "美年健康", "买入", "排板", None, "韩叔", None),
            ("2026年1月9日", "东湖高新", "买入", "排板", None, "韩叔", None),
            ("2026年1月9日", "辉煌科技", "买入", "排板", None, "韩叔", None),
            ("2026年1月9日", "蓝思科技", "买入", "排板", None, "韩叔", None),
            
            # 2026年1月5日 低吸策略
            ("2026年1月5日", "北斗星通", "买入", "低吸", None, "韩叔", None),
            ("2026年1月5日", "上海翰讯", "买入", "低吸", None, "韩叔", None),
            ("2026年1月5日", "陕西华达", "买入", "低吸", None, "韩叔", None),
            ("2026年1月5日", "久之洋", "买入", "低吸", None, "韩叔", None),
            
            # 2026年1月6日 低吸策略
            ("2026年1月6日", "立昂微", "买入", "低吸", None, "韩叔", None),
            
            # 2026年1月8日 排板策略（与上面的低吸策略是同一天）
            ("2026年1月8日", "东方明珠", "买入", "排板", None, "韩叔", None),
            ("2026年1月8日", "百利电气", "买入", "排板", None, "韩叔", None),
        ]
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        # 使用上下文推断日期：根据前面最近的完整日期来推断简化格式的年份
        last_full_date = None
        
        for date_str, stock_name, direction, strategy, price, source, notes in data:
            try:
                # 如果日期字符串包含完整年份，解析并保存作为参考
                if '年' in date_str or re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    date_obj = parse_chinese_date(date_str)
                    last_full_date = date_obj
                else:
                    # 简化格式，使用最近的完整日期作为参考
                    # 如果没有参考日期，使用当前日期
                    if last_full_date:
                        date_obj = parse_chinese_date(date_str, reference_date=last_full_date)
                    else:
                        date_obj = parse_chinese_date(date_str, reference_date=date.today())
                
                # 检查是否已存在相同的记录（同日期、同股票、同方向、同策略）
                from app.models.trading_calendar import TradingCalendar
                
                # 对于卖出操作，如果没有策略，使用空字符串；否则使用策略值
                strategy_filter = strategy if strategy else ""
                existing = db.query(TradingCalendar).filter(
                    TradingCalendar.date == date_obj,
                    TradingCalendar.stock_name == stock_name,
                    TradingCalendar.direction == direction,
                    TradingCalendar.strategy == strategy_filter
                ).first()
                
                if existing:
                    print(f"⏭️  跳过已存在记录: {date_obj} {stock_name} {direction} {strategy or ''}")
                    skip_count += 1
                    continue
                
                # 创建新记录
                # 对于卖出操作，如果没有策略，使用空字符串
                strategy_value = strategy if strategy else ""
                
                calendar_data = {
                    "date": date_obj,
                    "stock_name": stock_name,
                    "direction": direction,
                    "strategy": strategy_value,
                    "price": float(price) if price is not None else None,
                    "source": source,
                    "notes": notes,
                }
                
                TradingCalendarService.create(db, calendar_data)
                notes_str = f" 备注:{notes}" if notes else ""
                price_str = f" 价格:{price}" if price else ""
                strategy_str = f" {strategy}" if strategy else " (无策略)"
                print(f"✅ 成功导入: {date_obj} {stock_name} {direction}{strategy_str}{price_str}{notes_str}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 导入失败: {date_str} {stock_name} - {str(e)}")
                error_count += 1
                import traceback
                traceback.print_exc()
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
