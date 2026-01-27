"""
执行SQL文件脚本

使用方法:
    python scripts/execute_sql_file.py --file scripts/import_commercial_aerospace_satellite.sql
"""
import argparse
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database.session import SessionLocal
from sqlalchemy import text


def execute_sql_file(file_path: str):
    """执行SQL文件"""
    db = SessionLocal()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f"📁 执行SQL文件: {file_path}")
        print("-" * 60)
        
        # 分割SQL语句（按分号分割，但保留DO块）
        statements = []
        current_statement = ""
        in_do_block = False
        
        for line in sql_content.split('\n'):
            line_stripped = line.strip()
            
            # 检测DO块开始
            if 'DO $$' in line_stripped:
                in_do_block = True
                current_statement += line + '\n'
                continue
            
            # 检测DO块结束
            if in_do_block and 'END $$;' in line_stripped:
                current_statement += line + '\n'
                statements.append(current_statement.strip())
                current_statement = ""
                in_do_block = False
                continue
            
            current_statement += line + '\n'
            
            # 如果不是在DO块中，且遇到分号，结束当前语句
            if not in_do_block and line_stripped.endswith(';'):
                if current_statement.strip():
                    statements.append(current_statement.strip())
                current_statement = ""
        
        # 执行所有语句
        executed = 0
        for i, statement in enumerate(statements, 1):
            statement = statement.strip()
            if not statement or statement.startswith('--'):
                continue
            
            try:
                # 跳过验证查询（SELECT语句）
                if statement.upper().startswith('SELECT'):
                    print(f"\n📊 验证查询结果:")
                    result = db.execute(text(statement))
                    rows = result.fetchall()
                    if rows:
                        # 打印表头
                        if result.keys():
                            print("  " + " | ".join(result.keys()))
                            print("  " + "-" * 80)
                        # 打印数据
                        for row in rows:
                            print("  " + " | ".join(str(v) if v is not None else '' for v in row))
                    else:
                        print("  (无数据)")
                    continue
                
                # 执行SQL语句
                db.execute(text(statement))
                executed += 1
                
                # 提交事务（对于非SELECT语句）
                if not statement.upper().startswith('SELECT'):
                    db.commit()
                    
            except Exception as e:
                print(f"❌ 执行第 {i} 条语句时出错:")
                print(f"   {str(e)}")
                print(f"   语句: {statement[:100]}...")
                db.rollback()
                raise
        
        print(f"\n✅ SQL文件执行完成，共执行 {executed} 条语句")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return 1
    finally:
        db.close()
    
    return 0


def main():
    parser = argparse.ArgumentParser(description='执行SQL文件')
    parser.add_argument('--file', type=str, required=True, help='SQL文件路径')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 错误: 文件不存在: {args.file}")
        return 1
    
    return execute_sql_file(str(file_path))


if __name__ == '__main__':
    sys.exit(main())
