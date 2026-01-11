"""
导入涨停股涨停原因数据脚本（简化格式）

数据格式：个股\t涨停原因

使用方法:
    python scripts/import_limit_up_simple.py --date 2026-01-09 --file data.txt

或者直接使用文本数据:
    python scripts/import_limit_up_simple.py --date 2026-01-09 --text "个股\t涨停原因\n鲁信创投\t参投蓝箭航天 + 参投灵犀科创"
"""
import argparse
import re
from datetime import date
from pathlib import Path
from typing import Optional, Dict
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database.session import SessionLocal
from app.services.limit_up_board_service import LimitUpBoardService
from app.schemas.limit_up_board import LimitUpBoardCreate, parse_keywords_to_tags
from app.models.zt_pool import ZtPool
from app.utils.akshare_utils import safe_akshare_call
import akshare as ak


def get_stock_code_from_db(db, stock_name: str, target_date: date) -> Optional[str]:
    """
    从数据库中查找股票代码（优先从zt_pool表查找）
    """
    # 从zt_pool表查找
    zt_pool_item = db.query(ZtPool).filter(
        ZtPool.date == target_date,
        ZtPool.stock_name == stock_name
    ).first()
    
    if zt_pool_item and zt_pool_item.stock_code:
        return zt_pool_item.stock_code
    
    # 从limit_up_board表查找（可能之前已经导入过）
    from app.models.limit_up_board import LimitUpBoard
    limit_up_item = db.query(LimitUpBoard).filter(
        LimitUpBoard.stock_name == stock_name
    ).order_by(LimitUpBoard.date.desc()).first()
    
    if limit_up_item and limit_up_item.stock_code:
        return limit_up_item.stock_code
    
    return None


def get_stock_code_from_akshare(stock_name: str) -> Optional[str]:
    """
    使用akshare查找股票代码
    """
    try:
        # 方法1: 尝试使用 stock_info_a_code_name
        try:
            df = safe_akshare_call(ak.stock_info_a_code_name)
            if df is not None and not df.empty:
                # 查找匹配的股票名称
                matched = df[df['name'] == stock_name]
                if not matched.empty:
                    stock_code = matched.iloc[0]['code']
                    return str(stock_code).zfill(6)
                
                # 模糊匹配
                matched = df[df['name'].str.contains(stock_name, na=False)]
                if not matched.empty:
                    stock_code = matched.iloc[0]['code']
                    return str(stock_code).zfill(6)
        except Exception:
            pass
        
        # 方法2: 尝试使用 stock_zh_a_spot_em 获取实时数据（如果方法1失败）
        try:
            df = safe_akshare_call(ak.stock_zh_a_spot_em)
            if df is not None and not df.empty:
                # 查找匹配的股票名称
                matched = df[df['名称'] == stock_name]
                if not matched.empty:
                    stock_code = matched.iloc[0]['代码']
                    return str(stock_code).zfill(6)
                
                # 模糊匹配
                matched = df[df['名称'].str.contains(stock_name, na=False)]
                if not matched.empty:
                    stock_code = matched.iloc[0]['代码']
                    return str(stock_code).zfill(6)
        except Exception:
            pass
            
    except Exception as e:
        print(f"警告: 使用akshare查找股票代码失败 ({stock_name}): {e}")
    
    return None


def extract_board_name_from_reason(reason: str) -> str:
    """
    从涨停原因中提取板块名称
    尝试提取主要概念作为板块名称
    """
    if not reason:
        return "其他"
    
    # 常见板块关键词
    board_keywords = {
        "商业航天": ["商业航天", "航天", "卫星", "太空", "卫通"],
        "AI应用": ["AI", "人工智能", "大模型", "算力", "智能"],
        "AI营销": ["AI营销", "营销", "MCN", "字节", "抖音"],
        "AI医疗": ["AI医疗", "医疗", "健康", "医药", "基因"],
        "数据中心": ["数据中心", "液冷", "算力"],
        "机器人": ["机器人", "智能机器人", "仿生机器人"],
        "核电": ["核电", "核聚变"],
        "医药": ["医药", "药物", "创新药"],
        "半导体": ["半导体", "芯片", "GPU"],
        "有色": ["钨矿", "稀土", "钼", "锗"],
    }
    
    reason_lower = reason.lower()
    for board_name, keywords in board_keywords.items():
        for keyword in keywords:
            if keyword.lower() in reason_lower:
                return board_name
    
    # 如果没有匹配，返回"其他"
    return "其他"


def parse_simple_data(data_text: str, target_date: date, db) -> list[LimitUpBoardCreate]:
    """
    解析简化格式的数据（个股\t涨停原因）
    """
    items = []
    lines = data_text.strip().split('\n')
    
    # 构建股票代码缓存
    stock_code_cache: Dict[str, Optional[str]] = {}
    
    # 跳过表头（第一行）
    for line_num, line in enumerate(lines[1:], start=2):
        line = line.strip()
        if not line:
            continue
        
        # 使用制表符分割
        parts = [part.strip() for part in line.split('\t')]
        if len(parts) < 2:
            print(f"警告: 第 {line_num} 行数据格式不正确，跳过: {line[:50]}...")
            continue
        
        try:
            stock_name = parts[0]
            limit_up_reason = parts[1] if len(parts) > 1 else None
            
            if not stock_name:
                print(f"警告: 第 {line_num} 行股票名称为空，跳过")
                continue
            
            # 查找股票代码
            stock_code = None
            if stock_name in stock_code_cache:
                stock_code = stock_code_cache[stock_name]
            else:
                # 先从数据库查找
                stock_code = get_stock_code_from_db(db, stock_name, target_date)
                
                # 如果数据库中没有，使用akshare查找
                if not stock_code:
                    stock_code = get_stock_code_from_akshare(stock_name)
                
                stock_code_cache[stock_name] = stock_code
            
            if not stock_code:
                print(f"警告: 第 {line_num} 行无法找到股票代码 ({stock_name})，跳过")
                continue
            
            # 提取板块名称
            board_name = extract_board_name_from_reason(limit_up_reason) if limit_up_reason else "其他"
            
            # 解析关键字为标签和涨停原因
            keywords = limit_up_reason
            parsed_reason, tags = parse_keywords_to_tags(keywords)
            
            # 如果没有解析出原因，使用原始文本
            if not parsed_reason and limit_up_reason:
                parsed_reason = limit_up_reason
            
            item = LimitUpBoardCreate(
                date=target_date,
                board_name=board_name,
                board_stock_count=None,  # 无法从简化格式获取
                stock_code=stock_code,
                stock_name=stock_name,
                limit_up_days=None,  # 无法从简化格式获取
                limit_up_time=None,  # 无法从简化格式获取
                circulation_market_value=None,  # 无法从简化格式获取
                turnover_amount=None,  # 无法从简化格式获取
                keywords=keywords,
                limit_up_reason=parsed_reason,
                tags=tags
            )
            items.append(item)
        except Exception as e:
            print(f"错误: 第 {line_num} 行解析失败: {e}")
            print(f"  内容: {line[:100]}...")
            import traceback
            traceback.print_exc()
            continue
    
    return items


def main():
    parser = argparse.ArgumentParser(description='导入涨停股涨停原因数据（简化格式）')
    parser.add_argument('--date', type=str, required=True, help='日期，格式：YYYY-MM-DD')
    parser.add_argument('--file', type=str, default=None, help='数据文件路径')
    parser.add_argument('--text', type=str, default=None, help='直接提供数据文本（如果指定了--file则忽略此选项）')
    parser.add_argument('--delete-old', action='store_true', help='删除该日期的旧数据')
    parser.add_argument('--no-auto-extract', action='store_true', help='不自动从关键字提取概念板块')
    
    args = parser.parse_args()
    
    # 解析日期
    try:
        target_date = date.fromisoformat(args.date)
    except ValueError:
        print(f"错误: 日期格式错误，应为 YYYY-MM-DD，实际: {args.date}")
        return
    
    # 读取数据
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"错误: 文件不存在: {args.file}")
            return
        print(f"正在读取文件: {args.file}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data_text = f.read()
    elif args.text:
        print("使用命令行提供的数据文本")
        data_text = args.text
    else:
        print("错误: 必须提供 --file 或 --text 参数")
        return
    
    # 连接数据库
    db = SessionLocal()
    try:
        # 解析数据
        print(f"正在解析数据（日期: {target_date}）...")
        items = parse_simple_data(data_text, target_date, db)
        print(f"解析完成，共 {len(items)} 条记录")
        
        if not items:
            print("警告: 没有解析到任何数据")
            return
        
        # 如果需要，删除旧数据
        if args.delete_old:
            deleted_count = LimitUpBoardService.delete_by_date(db, target_date)
            print(f"已删除 {deleted_count} 条旧数据")
        
        # 批量导入
        print(f"正在导入数据到数据库...")
        auto_extract = not args.no_auto_extract
        LimitUpBoardService.batch_create(db, items, auto_extract)
        print(f"✓ 导入成功！共导入 {len(items)} 条记录")
        if auto_extract:
            print("✓ 已自动从关键字提取概念板块关联")
        
    except Exception as e:
        print(f"✗ 错误: 导入失败 - {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
