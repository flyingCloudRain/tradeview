"""
从文件导入交易日历数据
支持制表符分隔的文本文件格式

文件格式：
名称	操作	策略	时间	来源	价格	备注

执行方式：
    python backend/scripts/import_trading_calendar_from_file.py <文件路径>
"""
import sys
from pathlib import Path
import re
from datetime import date

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.services.trading_calendar_service import TradingCalendarService
from app.models.trading_calendar import TradingCalendar


def parse_chinese_date(date_str: str, reference_date: date = None) -> date:
    """
    解析中文日期格式
    支持格式：
    - "1月8日" -> 根据参考日期智能推断年份
    - "2025年12月22日" -> 2025-12-22
    - "2026年1月6日" -> 2026-01-06
    - "2026-01-09" -> 2026-01-09 (ISO格式)
    - "2026/01/09" -> 2026-01-09 (斜杠格式)
    - "20260109" -> 2026-01-09 (紧凑格式)
    
    Args:
        date_str: 日期字符串
        reference_date: 参考日期，用于推断简化格式的年份（默认为当前日期）
    
    Returns:
        解析后的日期对象
    
    Raises:
        ValueError: 如果日期格式无法识别或日期无效
    """
    if not date_str or not date_str.strip():
        raise ValueError("日期字符串不能为空")
    
    date_str = date_str.strip()
    original_str = date_str  # 保存原始字符串用于错误信息
    
    # 处理ISO格式 "2026-01-09"
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        try:
            return date.fromisoformat(date_str)
        except ValueError as e:
            raise ValueError(f"无效的ISO日期格式: {date_str} - {e}")
    
    # 处理斜杠格式 "2026/01/09" 或 "2026/1/9"
    match = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})$', date_str)
    if match:
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return date(year, month, day)
        except ValueError as e:
            raise ValueError(f"无效的斜杠日期格式: {date_str} - {e}")
    
    # 处理紧凑格式 "20260109"
    match = re.match(r'^(\d{4})(\d{2})(\d{2})$', date_str)
    if match:
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            return date(year, month, day)
        except ValueError as e:
            raise ValueError(f"无效的紧凑日期格式: {date_str} - {e}")
    
    # 处理完整格式 "2025年12月22日" 或 "2026年1月6日"
    match = re.match(r'^(\d{4})年(\d{1,2})月(\d{1,2})日$', date_str)
    if match:
        try:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            # 验证日期有效性
            if not (1 <= month <= 12):
                raise ValueError(f"月份必须在1-12之间: {month}")
            if not (1 <= day <= 31):
                raise ValueError(f"日期必须在1-31之间: {day}")
            return date(year, month, day)
        except ValueError as e:
            raise ValueError(f"无效的中文日期格式: {date_str} - {e}")
    
    # 处理简化格式 "1月8日" (智能推断年份)
    match = re.match(r'^(\d{1,2})月(\d{1,2})日$', date_str)
    if match:
        try:
            month, day = int(match.group(1)), int(match.group(2))
            
            # 验证月份和日期范围
            if not (1 <= month <= 12):
                raise ValueError(f"月份必须在1-12之间: {month}")
            if not (1 <= day <= 31):
                raise ValueError(f"日期必须在1-31之间: {day}")
            
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
        except ValueError as e:
            raise ValueError(f"无效的简化日期格式: {date_str} - {e}")
    
    # 如果所有格式都不匹配，抛出详细错误
    raise ValueError(
        f"无法解析日期格式: {original_str!r}。"
        f"支持的格式: '2026年1月9日', '2026-01-09', '2026/01/09', '20260109', '1月9日'"
    )


def parse_price(price_str: str) -> float | None:
    """解析价格字符串"""
    if not price_str or not price_str.strip():
        return None
    try:
        return float(price_str.strip())
    except ValueError:
        return None


def import_from_file(file_path: str):
    """从文件导入交易日历数据"""
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    db = SessionLocal()
    
    try:
        success_count = 0
        skip_count = 0
        error_count = 0
        
        # 使用上下文推断日期：根据前面最近的完整日期来推断简化格式的年份
        last_full_date = None
        
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 跳过表头（第一行）
        data_lines = lines[1:] if len(lines) > 1 else []
        
        for line_num, line in enumerate(data_lines, start=2):
            line = line.strip()
            if not line:
                continue
            
            try:
                # 按制表符分割
                parts = line.split('\t')
                if len(parts) < 5:
                    print(f"⚠️  第 {line_num} 行格式不正确，跳过: {line}")
                    error_count += 1
                    continue
                
                # 解析各字段
                stock_name = parts[0].strip()
                direction = parts[1].strip()
                strategy = parts[2].strip() if len(parts) > 2 else ""
                date_str = parts[3].strip() if len(parts) > 3 else ""
                source = parts[4].strip() if len(parts) > 4 else ""
                price_str = parts[5].strip() if len(parts) > 5 else ""
                notes = parts[6].strip() if len(parts) > 6 else ""
                
                # 验证必填字段
                if not stock_name:
                    print(f"⚠️  第 {line_num} 行股票名称为空，跳过")
                    error_count += 1
                    continue
                
                if not direction:
                    print(f"⚠️  第 {line_num} 行操作方向为空，跳过")
                    error_count += 1
                    continue
                
                if not date_str:
                    print(f"⚠️  第 {line_num} 行日期为空，跳过")
                    error_count += 1
                    continue
                
                # 解析日期
                if '年' in date_str or re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                    date_obj = parse_chinese_date(date_str)
                    last_full_date = date_obj
                else:
                    # 简化格式，使用最近的完整日期作为参考
                    if last_full_date:
                        date_obj = parse_chinese_date(date_str, reference_date=last_full_date)
                    else:
                        date_obj = parse_chinese_date(date_str, reference_date=date.today())
                
                # 解析价格
                price = parse_price(price_str)
                
                # 处理策略：卖出操作可能没有策略
                strategy_value = strategy if strategy else ""
                
                # 处理空值
                source_value = source if source else None
                notes_value = notes if notes else None
                
                # 检查是否已存在相同的记录（同日期、同股票、同方向、同策略）
                strategy_filter = strategy_value if strategy_value else ""
                existing = db.query(TradingCalendar).filter(
                    TradingCalendar.date == date_obj,
                    TradingCalendar.stock_name == stock_name,
                    TradingCalendar.direction == direction,
                    TradingCalendar.strategy == strategy_filter
                ).first()
                
                if existing:
                    print(f"⏭️  跳过已存在记录: {date_obj} {stock_name} {direction} {strategy_value or '(无策略)'}")
                    skip_count += 1
                    continue
                
                # 创建新记录
                calendar_data = {
                    "date": date_obj,
                    "stock_name": stock_name,
                    "direction": direction,
                    "strategy": strategy_value,
                    "price": price,
                    "source": source_value,
                    "notes": notes_value,
                }
                
                TradingCalendarService.create(db, calendar_data)
                notes_str = f" 备注:{notes_value}" if notes_value else ""
                price_str = f" 价格:{price}" if price else ""
                strategy_str = f" {strategy_value}" if strategy_value else " (无策略)"
                print(f"✅ 成功导入: {date_obj} {stock_name} {direction}{strategy_str}{price_str}{notes_str}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 第 {line_num} 行导入失败: {line} - {str(e)}")
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


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python import_trading_calendar_from_file.py <文件路径>")
        print("文件格式: 制表符分隔，第一行为表头")
        print("列: 名称\t操作\t策略\t时间\t来源\t价格\t备注")
        sys.exit(1)
    
    file_path = sys.argv[1]
    import_from_file(file_path)


if __name__ == "__main__":
    main()
