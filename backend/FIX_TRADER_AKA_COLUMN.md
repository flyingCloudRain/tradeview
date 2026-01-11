# 修复 trader 表缺少 aka 列的问题

## 问题描述

数据库报错：`column trader.aka does not exist`

这是因为数据库中的 `trader` 表缺少 `aka` 列，虽然迁移文件中已经定义了该列，但可能迁移没有正确执行，或者表是通过其他方式创建的。

## 解决方案

### 方法一：执行 Alembic 迁移（推荐）

运行以下命令来执行迁移，添加缺失的 `aka` 列：

```bash
cd backend
alembic upgrade head
```

这将执行所有未应用的迁移，包括：
1. `change_trader_aka_comment` - 更新字段注释
2. `add_aka_column_to_trader` - 检查并添加 `aka` 列（如果不存在）

### 方法二：手动执行 SQL（如果迁移失败）

如果迁移执行失败，可以直接在数据库中执行以下 SQL：

**PostgreSQL:**
```sql
-- 检查列是否存在
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'trader' AND column_name = 'aka';

-- 如果列不存在，添加列
ALTER TABLE trader ADD COLUMN IF NOT EXISTS aka TEXT;

-- 添加注释
COMMENT ON COLUMN trader.aka IS '描述';
```

**SQLite:**
```sql
-- SQLite 不支持 IF NOT EXISTS，需要先检查
-- 如果列不存在，添加列
ALTER TABLE trader ADD COLUMN aka TEXT;
```

### 方法三：使用 Python 脚本修复

创建一个临时脚本来检查和修复：

```python
# fix_trader_aka.py
from app.database.session import SessionLocal, engine
from sqlalchemy import text, inspect

db = SessionLocal()
try:
    # 检查列是否存在
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns('trader')]
    
    if 'aka' not in columns:
        print("添加 aka 列...")
        db.execute(text("ALTER TABLE trader ADD COLUMN aka TEXT"))
        db.commit()
        print("✅ 已添加 aka 列")
    else:
        print("✅ aka 列已存在")
finally:
    db.close()
```

运行：
```bash
cd backend
python fix_trader_aka.py
```

## 验证

执行迁移后，可以通过以下方式验证：

```python
from app.database.session import SessionLocal
from app.models.lhb import Trader

db = SessionLocal()
try:
    traders = db.query(Trader).limit(1).all()
    print(f"✅ 查询成功，找到 {len(traders)} 个游资")
    if traders:
        print(f"示例: {traders[0].name}, aka: {traders[0].aka}")
finally:
    db.close()
```

## 注意事项

1. 执行迁移前建议备份数据库
2. 如果使用的是生产环境，请在维护窗口期间执行
3. 迁移会自动检查列是否存在，不会重复添加
