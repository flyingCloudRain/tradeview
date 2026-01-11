"""
生成完整的游资和机构关联SQL导入脚本
执行：PYTHONPATH=. python backend/scripts/generate_traders_sql.py
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.import_traders_detailed import TRADERS_DATA, parse_traders_data


def escape_sql_string(s: str) -> str:
    """转义SQL字符串中的特殊字符"""
    if not s:
        return "''"
    # 转义单引号
    s = s.replace("'", "''")
    return f"'{s}'"


def generate_sql_script():
    """生成完整的SQL导入脚本"""
    print("解析游资数据...")
    traders_data = parse_traders_data(TRADERS_DATA)
    print(f"解析完成，共 {len(traders_data)} 个游资")
    
    sql_lines = []
    sql_lines.append("-- 游资和游资机构完整导入SQL脚本")
    sql_lines.append("-- 生成时间: " + str(Path(__file__).stat().st_mtime))
    sql_lines.append("--")
    sql_lines.append("-- 执行方式：")
    sql_lines.append("--   PostgreSQL: psql -h <host> -U <user> -d <database> -f import_traders_complete.sql")
    sql_lines.append("")
    sql_lines.append("-- 开始事务")
    sql_lines.append("BEGIN;")
    sql_lines.append("")
    sql_lines.append("-- ========================================")
    sql_lines.append("-- 第一部分：插入游资主体数据")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    
    # 生成游资INSERT语句
    trader_values = []
    for trader in traders_data:
        name = escape_sql_string(trader['name'])
        description = escape_sql_string(trader['description'])
        trader_values.append(f"({name}, {description}, NOW(), NOW())")
    
    sql_lines.append("INSERT INTO trader (name, aka, created_at, updated_at) VALUES")
    sql_lines.append(",\n".join(trader_values))
    sql_lines.append("ON CONFLICT (name) DO UPDATE SET")
    sql_lines.append("    aka = EXCLUDED.aka,")
    sql_lines.append("    updated_at = NOW();")
    sql_lines.append("")
    
    # 生成机构关联INSERT语句
    sql_lines.append("-- ========================================")
    sql_lines.append("-- 第二部分：插入游资机构关联数据")
    sql_lines.append("-- ========================================")
    sql_lines.append("")
    sql_lines.append("-- 注意：由于需要关联trader_id，使用子查询获取ID")
    sql_lines.append("")
    
    branch_values = []
    total_branches = 0
    
    for trader in traders_data:
        trader_name = trader['name']
        for branch in trader['branches']:
            institution_name = escape_sql_string(branch['name'])
            institution_code = escape_sql_string(branch.get('code') or '')
            if institution_code == "''":
                institution_code = "NULL"
            
            # 使用子查询获取trader_id
            branch_values.append(
                f"((SELECT id FROM trader WHERE name = {escape_sql_string(trader_name)}), "
                f"{institution_name}, {institution_code})"
            )
            total_branches += 1
    
    sql_lines.append(f"-- 共 {total_branches} 个机构关联")
    sql_lines.append("INSERT INTO trader_branch (trader_id, institution_name, institution_code) VALUES")
    sql_lines.append(",\n".join(branch_values))
    sql_lines.append("ON CONFLICT (trader_id, institution_name) DO UPDATE SET")
    sql_lines.append("    institution_code = COALESCE(EXCLUDED.institution_code, trader_branch.institution_code),")
    sql_lines.append("    updated_at = NOW();")
    sql_lines.append("")
    
    sql_lines.append("-- 提交事务")
    sql_lines.append("COMMIT;")
    sql_lines.append("")
    sql_lines.append(f"-- 导入完成：{len(traders_data)} 个游资，{total_branches} 个机构关联")
    
    # 写入文件
    output_file = Path(__file__).parent / "import_traders_complete.sql"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))
    
    print(f"\n✅ SQL脚本已生成: {output_file}")
    print(f"   游资主体: {len(traders_data)} 个")
    print(f"   机构关联: {total_branches} 个")
    print(f"\n执行方式:")
    print(f"   PostgreSQL: psql -h <host> -U <user> -d <database> -f {output_file}")


if __name__ == "__main__":
    generate_sql_script()
