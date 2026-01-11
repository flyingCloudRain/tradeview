"""
导入涨停板分析数据脚本

使用方法:
    python scripts/import_limit_up_board.py --date 2025-01-20 --file data.txt

数据格式示例（制表符分隔）:
    板块	涨停天数	代码	个股	涨停时间	流通市值（亿元）	成交额（亿元）	涨停关键词
    商业航天 * 29	11 天 9 板	600783.SH	鲁信创投	9:25:00	242.6	2.1	参投蓝箭航天 + 参投灵犀科创 + 创投 + 银座股份公司
"""
import argparse
import re
from datetime import date, time
from pathlib import Path
from typing import Optional
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import SessionLocal
from app.services.limit_up_board_service import LimitUpBoardService
from app.schemas.limit_up_board import LimitUpBoardCreate, parse_keywords_to_tags


def parse_board_name(board_str: str) -> tuple[str, Optional[int]]:
    """
    解析板块名称和数量
    例如: "商业航天 * 29" -> ("商业航天", 29)
    """
    # 匹配格式: "板块名称 * 数量"
    match = re.match(r'^(.+?)\s*\*\s*(\d+)$', board_str.strip())
    if match:
        board_name = match.group(1).strip()
        board_count = int(match.group(2))
        return board_name, board_count
    # 如果没有数量，只返回板块名称
    return board_str.strip(), None


def parse_time(time_str: str) -> Optional[time]:
    """解析时间字符串"""
    if not time_str or not time_str.strip():
        return None
    try:
        # 支持 HH:MM:SS 或 HH:MM 格式
        parts = time_str.strip().split(':')
        if len(parts) == 2:
            return time(int(parts[0]), int(parts[1]))
        elif len(parts) == 3:
            return time(int(parts[0]), int(parts[1]), int(parts[2]))
    except (ValueError, IndexError):
        pass
    return None


def parse_float(value: str) -> Optional[float]:
    """解析浮点数"""
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None


def parse_data_file(file_path: str, target_date: date) -> list[LimitUpBoardCreate]:
    """
    解析数据文件
    """
    items = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 跳过表头（第一行）
    for line_num, line in enumerate(lines[1:], start=2):
        line = line.strip()
        if not line:
            continue
        
        # 使用制表符分割
        parts = [part.strip() for part in line.split('\t')]
        if len(parts) < 4:
            print(f"警告: 第 {line_num} 行数据格式不正确，跳过: {line[:50]}...")
            continue
        
        try:
            board_str = parts[0]
            limit_up_days = parts[1] if len(parts) > 1 else None
            stock_code = parts[2] if len(parts) > 2 else None
            stock_name = parts[3] if len(parts) > 3 else None
            limit_up_time_str = parts[4] if len(parts) > 4 else None
            circulation_market_value_str = parts[5] if len(parts) > 5 else None
            turnover_amount_str = parts[6] if len(parts) > 6 else None
            keywords = parts[7] if len(parts) > 7 else None
            
            # 解析板块名称和数量
            board_name, board_count = parse_board_name(board_str)
            
            # 解析时间
            limit_up_time = parse_time(limit_up_time_str) if limit_up_time_str else None
            
            # 解析数值
            circulation_market_value = parse_float(circulation_market_value_str)
            turnover_amount = parse_float(turnover_amount_str)
            
            # 解析关键字为标签和涨停原因
            limit_up_reason, tags = parse_keywords_to_tags(keywords)
            
            item = LimitUpBoardCreate(
                date=target_date,
                board_name=board_name,
                board_stock_count=board_count,
                stock_code=stock_code,
                stock_name=stock_name,
                limit_up_days=limit_up_days,
                limit_up_time=limit_up_time,
                circulation_market_value=circulation_market_value,
                turnover_amount=turnover_amount,
                keywords=keywords,
                limit_up_reason=limit_up_reason,
                tags=tags
            )
            items.append(item)
        except Exception as e:
            print(f"错误: 第 {line_num} 行解析失败: {e}")
            print(f"  内容: {line[:100]}...")
            continue
    
    return items


def main():
    parser = argparse.ArgumentParser(description='导入涨停板分析数据')
    parser.add_argument('--date', type=str, required=True, help='日期，格式：YYYY-MM-DD')
    parser.add_argument('--file', type=str, required=True, help='数据文件路径')
    parser.add_argument('--delete-old', action='store_true', help='删除该日期的旧数据')
    parser.add_argument('--no-auto-extract', action='store_true', help='不自动从关键字提取概念板块')
    
    args = parser.parse_args()
    
    # 解析日期
    try:
        target_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"错误: 日期格式错误，应为 YYYY-MM-DD，实际: {args.date}")
        return
    
    # 检查文件是否存在
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在: {args.file}")
        return
    
    # 解析数据
    print(f"正在解析数据文件: {args.file}")
    items = parse_data_file(str(file_path), target_date)
    print(f"解析完成，共 {len(items)} 条记录")
    
    if not items:
        print("警告: 没有解析到任何数据")
        return
    
    # 连接数据库
    db = SessionLocal()
    try:
        # 如果需要，删除旧数据
        if args.delete_old:
            deleted_count = LimitUpBoardService.delete_by_date(db, target_date)
            print(f"已删除 {deleted_count} 条旧数据")
        
        # 批量导入
        print(f"正在导入数据到数据库...")
        auto_extract = not args.no_auto_extract
        LimitUpBoardService.batch_create(db, items, auto_extract)
        print(f"导入成功！共导入 {len(items)} 条记录")
        if auto_extract:
            print("已自动从关键字提取概念板块关联")
        
    except Exception as e:
        print(f"错误: 导入失败 - {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
