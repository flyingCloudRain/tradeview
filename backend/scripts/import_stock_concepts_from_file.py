"""
导入涨停个股概念数据脚本

使用方法:
    python scripts/import_stock_concepts_from_file.py --file data.txt --date 2026-01-09

数据格式:
    个股	概念
    鲁信创投	参投蓝箭航天 + 参投灵犀科创 + 创投 + 银座股份公司
    金风科技	参投蓝箭航天 + 军工 + 机械 + 风电 + 新疆
"""
import argparse
import sys
from pathlib import Path
from datetime import date
from typing import List, Set

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.stock_concept import StockConcept, StockConceptMapping
from app.services.stock_concept_service import StockConceptService, StockConceptMappingService


def parse_concepts(concept_str: str) -> List[str]:
    """
    解析概念字符串，返回概念列表（去重）
    例如: "参投蓝箭航天 + 参投灵犀科创 + 创投" -> ["参投蓝箭航天", "参投灵犀科创", "创投"]
    """
    if not concept_str or not concept_str.strip():
        return []
    
    # 使用 + 分割，并清理空白
    concepts = [c.strip() for c in concept_str.split('+')]
    # 过滤空字符串并去重（保持顺序）
    seen = set()
    unique_concepts = []
    for c in concepts:
        if c and c not in seen:
            seen.add(c)
            unique_concepts.append(c)
    return unique_concepts


def get_or_create_concept(db, concept_name: str) -> StockConcept:
    """
    获取或创建概念板块
    """
    concept = StockConceptService.get_by_name(db, concept_name)
    if concept:
        return concept
    
    # 创建新概念
    concept_data = {"name": concept_name}
    concept = StockConceptService.create(db, concept_data)
    return concept


def parse_data_file(file_path: str) -> List[tuple[str, List[str]]]:
    """
    解析数据文件，返回 (股票名称, 概念列表) 的列表
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
        if len(parts) < 2:
            print(f"警告: 第 {line_num} 行数据格式不正确，跳过: {line[:50]}...")
            continue
        
        stock_name = parts[0]
        concept_str = parts[1] if len(parts) > 1 else ""
        
        # 解析概念
        concepts = parse_concepts(concept_str)
        
        if not stock_name:
            print(f"警告: 第 {line_num} 行股票名称为空，跳过")
            continue
        
        items.append((stock_name, concepts))
    
    return items


def import_stock_concepts(file_path: str, target_date: date = None, replace_existing: bool = False):
    """
    导入股票概念数据
    
    Args:
        file_path: 数据文件路径
        target_date: 目标日期（可选，用于日志记录）
        replace_existing: 是否替换现有关联（默认False，追加模式）
    """
    # 解析数据文件
    print(f"正在解析数据文件: {file_path}")
    items = parse_data_file(file_path)
    print(f"解析完成，共 {len(items)} 条记录")
    
    if not items:
        print("警告: 没有解析到任何数据")
        return
    
    # 连接数据库
    db = SessionLocal()
    try:
        # 统计信息
        concepts_created = 0
        concepts_existing = 0
        mappings_created = 0
        mappings_existing = 0
        
        # 处理每条记录
        for stock_name, concept_names in items:
            if not concept_names:
                print(f"跳过 {stock_name}: 无概念数据")
                continue
            
            # 获取或创建概念板块
            concept_ids = []
            for concept_name in concept_names:
                # 先检查是否存在
                existing_concept = StockConceptService.get_by_name(db, concept_name)
                if existing_concept:
                    concept_ids.append(existing_concept.id)
                    concepts_existing += 1
                else:
                    # 创建新概念
                    concept = get_or_create_concept(db, concept_name)
                    concept_ids.append(concept.id)
                    concepts_created += 1
            
            # 处理股票概念关联
            if replace_existing:
                # 替换模式：先删除现有关联
                StockConceptMappingService.set_concepts_for_stock(db, stock_name, concept_ids)
                mappings_created += len(concept_ids)
                print(f"已更新 {stock_name}: {len(concept_ids)} 个概念")
            else:
                # 追加模式：只添加不存在的关联
                stock_mappings_count = 0
                for concept_id in concept_ids:
                    existing = db.query(StockConceptMapping).filter(
                        StockConceptMapping.stock_name == stock_name,
                        StockConceptMapping.concept_id == concept_id
                    ).first()
                    
                    if not existing:
                        mapping = StockConceptMapping(
                            stock_name=stock_name,
                            concept_id=concept_id
                        )
                        db.add(mapping)
                        mappings_created += 1
                        stock_mappings_count += 1
                    else:
                        mappings_existing += 1
                
                print(f"已处理 {stock_name}: 新增 {stock_mappings_count} 个概念关联")
        
        # 提交所有更改
        db.commit()
        
        # 打印统计信息
        print("\n" + "="*50)
        print("导入统计:")
        print(f"  概念板块 - 新建: {concepts_created}, 已存在: {concepts_existing}")
        print(f"  股票概念关联 - 新建: {mappings_created}, 已存在: {mappings_existing}")
        print(f"  总计处理股票数: {len(items)}")
        if target_date:
            print(f"  目标日期: {target_date}")
        print("="*50)
        
    except Exception as e:
        print(f"错误: 导入失败 - {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='导入涨停个股概念数据')
    parser.add_argument('--file', type=str, required=True, help='数据文件路径')
    parser.add_argument('--date', type=str, help='日期，格式：YYYY-MM-DD（可选，用于日志记录）')
    parser.add_argument('--replace', action='store_true', help='替换现有关联（默认追加模式）')
    
    args = parser.parse_args()
    
    # 解析日期（可选）
    target_date = None
    if args.date:
        try:
            target_date = date.fromisoformat(args.date)
        except ValueError:
            print(f"警告: 日期格式错误，应为 YYYY-MM-DD，实际: {args.date}")
            print("继续执行，但不记录日期信息")
    
    # 检查文件是否存在
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在: {args.file}")
        return
    
    # 导入数据
    import_stock_concepts(str(file_path), target_date, args.replace)


if __name__ == '__main__':
    main()
