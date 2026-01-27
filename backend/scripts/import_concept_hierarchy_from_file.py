"""
导入层级概念和股票数据脚本

使用方法:
    python scripts/import_concept_hierarchy_from_file.py --file data.txt

数据格式（制表符分隔）:
    一级概念	二级概念	三级概念	个股列表（用、分隔）
    商业航天	卫星	卫星制造	航天发展、中国卫星、银河电子
    商业航天	卫星	零部件	乾照光电、神钢股份
    商业航天	火箭回收	智慧测控船	海兰信

说明:
    - 如果三级概念为空，股票将关联到二级概念
    - 如果二级概念也为空，股票将关联到一级概念
    - 自动创建概念层级结构
    - 自动处理重复数据（幂等性）
"""
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Optional
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from app.models.stock_concept import StockConcept, StockConceptMapping
from app.services.stock_concept_service import StockConceptService, StockConceptMappingService


def parse_stocks(stock_str: str) -> List[str]:
    """
    解析股票字符串，返回股票列表（去重）
    例如: "航天发展、中国卫星、银河电子" -> ["航天发展", "中国卫星", "银河电子"]
    """
    if not stock_str or not stock_str.strip():
        return []
    
    # 使用 、分割，并清理空白
    stocks = [s.strip() for s in stock_str.split('、')]
    # 过滤空字符串并去重（保持顺序）
    seen = set()
    unique_stocks = []
    for s in stocks:
        if s and s not in seen:
            seen.add(s)
            unique_stocks.append(s)
    return unique_stocks


def parse_data_file(file_path: str) -> List[Tuple[str, Optional[str], Optional[str], List[str]]]:
    """
    解析数据文件，返回 (一级概念, 二级概念, 三级概念, 股票列表) 的列表
    
    Returns:
        List of tuples: (level1, level2, level3, stocks)
    """
    items = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        
        # 使用制表符分割
        parts = [part.strip() for part in line.split('\t')]
        
        # 至少需要一级概念和股票列表
        if len(parts) < 2:
            print(f"警告: 第 {line_num} 行数据格式不正确，跳过: {line[:50]}...")
            continue
        
        level1 = parts[0] if len(parts) > 0 and parts[0] else None
        level2 = parts[1] if len(parts) > 1 and parts[1] else None
        level3 = parts[2] if len(parts) > 2 and parts[2] else None
        stocks_str = parts[3] if len(parts) > 3 and parts[3] else ""
        
        if not level1:
            print(f"警告: 第 {line_num} 行一级概念为空，跳过")
            continue
        
        # 解析股票列表
        stocks = parse_stocks(stocks_str)
        
        if not stocks:
            print(f"警告: 第 {line_num} 行无股票数据，跳过")
            continue
        
        items.append((level1, level2, level3, stocks))
    
    return items


def get_or_create_concept(
    db, 
    concept_name: str, 
    parent_id: Optional[int] = None, 
    sort_order: int = 0
) -> Tuple[StockConcept, bool]:
    """
    获取或创建概念板块
    
    Returns:
        (concept, is_new): 概念对象和是否新建的标识
    """
    # 先查找是否存在同名概念
    concept = StockConceptService.get_by_name(db, concept_name)
    
    if concept:
        # 如果存在，检查parent_id是否匹配
        if parent_id is not None and concept.parent_id != parent_id:
            # 更新parent_id
            update_data = {'parent_id': parent_id}
            concept = StockConceptService.update(db, concept.id, update_data)
        return concept, False
    
    # 创建新概念
    concept_data = {
        "name": concept_name,
        "parent_id": parent_id,
        "sort_order": sort_order
    }
    concept = StockConceptService.create(db, concept_data)
    return concept, True


def import_concept_hierarchy(file_path: str):
    """
    导入层级概念和股票数据
    
    Args:
        file_path: 数据文件路径
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
        concepts_created = defaultdict(int)  # {level: count}
        concepts_existing = defaultdict(int)
        mappings_created = 0
        mappings_existing = 0
        
        # 用于跟踪已创建的概念，避免重复查询
        concept_cache = {}  # {(name, parent_id): concept}
        
        # 处理每条记录
        for idx, (level1_name, level2_name, level3_name, stocks) in enumerate(items, 1):
            print(f"\n处理第 {idx}/{len(items)} 条记录:")
            print(f"  一级: {level1_name}, 二级: {level2_name or '(空)'}, 三级: {level3_name or '(空)'}")
            print(f"  股票数: {len(stocks)}")
            
            # 步骤1：创建或获取一级概念
            level1_key = (level1_name, None)
            if level1_key in concept_cache:
                level1_concept = concept_cache[level1_key]
                is_new1 = False
            else:
                level1_concept, is_new1 = get_or_create_concept(db, level1_name, None, 0)
                concept_cache[level1_key] = level1_concept
                if is_new1:
                    concepts_created[1] += 1
                    print(f"  ✅ 创建一级概念: {level1_name} (ID: {level1_concept.id})")
                else:
                    concepts_existing[1] += 1
                    print(f"  ⚠️  一级概念已存在: {level1_name} (ID: {level1_concept.id})")
            
            # 确定目标概念（最深层级的概念）
            target_concept = level1_concept
            target_level = 1
            
            # 步骤2：如果有二级概念，创建或获取二级概念
            if level2_name:
                level2_key = (level2_name, level1_concept.id)
                if level2_key in concept_cache:
                    level2_concept = concept_cache[level2_key]
                    is_new2 = False
                else:
                    level2_concept, is_new2 = get_or_create_concept(db, level2_name, level1_concept.id, 0)
                    concept_cache[level2_key] = level2_concept
                    if is_new2:
                        concepts_created[2] += 1
                        print(f"  ✅ 创建二级概念: {level2_name} (ID: {level2_concept.id})")
                    else:
                        concepts_existing[2] += 1
                        print(f"  ⚠️  二级概念已存在: {level2_name} (ID: {level2_concept.id})")
                
                target_concept = level2_concept
                target_level = 2
                
                # 步骤3：如果有三级概念，创建或获取三级概念
                if level3_name:
                    level3_key = (level3_name, level2_concept.id)
                    if level3_key in concept_cache:
                        level3_concept = concept_cache[level3_key]
                        is_new3 = False
                    else:
                        level3_concept, is_new3 = get_or_create_concept(db, level3_name, level2_concept.id, 0)
                        concept_cache[level3_key] = level3_concept
                        if is_new3:
                            concepts_created[3] += 1
                            print(f"  ✅ 创建三级概念: {level3_name} (ID: {level3_concept.id})")
                        else:
                            concepts_existing[3] += 1
                            print(f"  ⚠️  三级概念已存在: {level3_name} (ID: {level3_concept.id})")
                    
                    target_concept = level3_concept
                    target_level = 3
            
            # 步骤4：关联股票到目标概念
            print(f"  关联股票到{target_level}级概念: {target_concept.name}")
            for stock_name in stocks:
                try:
                    result = StockConceptMappingService.add_concept_to_stock(
                        db, stock_name, target_concept.id
                    )
                    if result:
                        mappings_created += 1
                        print(f"    ✅ 关联: {stock_name}")
                    else:
                        mappings_existing += 1
                        print(f"    ⚠️  已存在: {stock_name}")
                except Exception as e:
                    # 检查是否是因为已存在
                    existing = db.query(StockConceptMapping).filter(
                        StockConceptMapping.stock_name == stock_name,
                        StockConceptMapping.concept_id == target_concept.id
                    ).first()
                    if existing:
                        mappings_existing += 1
                        print(f"    ⚠️  已存在: {stock_name}")
                    else:
                        print(f"    ❌ 关联失败: {stock_name} - {e}")
        
        # 步骤5：更新stock_count统计字段
        print("\n更新stock_count统计字段...")
        concepts = db.query(StockConcept).all()
        for concept in concepts:
            count = db.query(StockConceptMapping).filter(
                StockConceptMapping.concept_id == concept.id
            ).count()
            concept.stock_count = count
        
        db.commit()
        
        # 打印统计信息
        print("\n" + "="*60)
        print("📊 导入统计:")
        print(f"  概念创建:")
        for level in sorted(concepts_created.keys()):
            print(f"    {level}级 - 新建: {concepts_created[level]}, 已存在: {concepts_existing.get(level, 0)}")
        print(f"  股票概念关联 - 新建: {mappings_created}, 已存在: {mappings_existing}")
        print(f"  总计处理记录数: {len(items)}")
        print("="*60)
        
        print("\n✅ 导入完成！")
        
    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description='导入层级概念和股票数据')
    parser.add_argument('--file', type=str, required=True, help='数据文件路径')
    
    args = parser.parse_args()
    
    # 检查文件是否存在
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在: {args.file}")
        return 1
    
    # 导入数据
    try:
        import_concept_hierarchy(str(file_path))
        return 0
    except Exception as e:
        print(f"错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
