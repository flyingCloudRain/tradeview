# 游资数据导入指南

本文档说明如何导入游资和游资机构数据到数据库。

## 方法一：使用Python脚本（推荐）

这是最简单和推荐的方法，支持自动处理数据关联和去重。

### 执行命令

```bash
# 在项目根目录执行
PYTHONPATH=. python backend/scripts/import_traders_detailed.py
```

### 功能特点

- ✅ 自动解析游资数据
- ✅ 自动创建/更新游资记录
- ✅ 自动处理机构关联
- ✅ 支持强制重新导入模式
- ✅ 自动去重处理
- ✅ 详细的导入日志

### 参数说明

脚本默认使用 `force_reimport=True`，会删除并重新创建所有机构关联。

如果需要增量更新（不删除现有关联），可以修改脚本中的 `main()` 调用：

```python
main(force_reimport=False)  # 增量更新模式
```

## 方法二：使用SQL脚本

### 步骤1：生成完整SQL脚本

```bash
PYTHONPATH=. python backend/scripts/generate_traders_sql.py
```

这会生成 `import_traders_complete.sql` 文件，包含所有游资和机构关联数据。

### 步骤2：执行SQL脚本

#### PostgreSQL

```bash
# 使用psql命令行工具
psql -h <host> -U <user> -d <database> -f backend/scripts/import_traders_complete.sql

# 或者使用环境变量中的连接字符串
psql $DATABASE_URL -f backend/scripts/import_traders_complete.sql
```

### 注意事项

- SQL脚本使用 `ON CONFLICT` 语法处理重复数据（PostgreSQL）
- 确保数据库表已创建（运行过migration）

## 方法三：使用简化SQL脚本（仅游资主体）

如果只需要导入游资主体数据（不包含机构关联），可以使用：

```bash
# PostgreSQL
psql $DATABASE_URL -f backend/scripts/import_traders.sql
```

**注意**：此脚本只包含88个游资主体，不包含296个机构关联。完整的机构关联数据需要使用Python脚本或完整SQL脚本。

## 数据统计

- **游资主体**: 88 个
- **机构关联**: 296 个

## 验证导入结果

### 使用SQL查询

```sql
-- 查询游资总数
SELECT COUNT(*) FROM trader;

-- 查询机构关联总数
SELECT COUNT(*) FROM trader_branch;

-- 查询某个游资及其机构
SELECT t.name, t.aka, COUNT(tb.id) as branch_count
FROM trader t
LEFT JOIN trader_branch tb ON t.id = tb.trader_id
GROUP BY t.id, t.name, t.aka
ORDER BY branch_count DESC
LIMIT 10;
```

### 使用Python验证

```python
from app.database.session import SessionLocal
from app.models.lhb import Trader, TraderBranch

session = SessionLocal()
try:
    trader_count = session.query(Trader).count()
    branch_count = session.query(TraderBranch).count()
    print(f"游资主体: {trader_count} 个")
    print(f"机构关联: {branch_count} 个")
finally:
    session.close()
```

## 故障排除

### 问题1：导入失败，提示表不存在

**解决方案**：先运行数据库迁移

```bash
cd backend
alembic upgrade head
```

### 问题2：PostgreSQL连接失败

**解决方案**：检查环境变量

```bash
# 设置数据库连接
export DATABASE_URL="postgresql://user:password@host:port/database"

# 或使用setup脚本
source backend/setup_env.sh
```


## 推荐方案

**推荐使用方法一（Python脚本）**，因为：

1. ✅ 自动处理数据关联和去重
2. ✅ 详细的错误处理和日志
3. ✅ 支持增量更新和强制重新导入
4. ✅ 自动查找现有机构代码

## 相关文件

- `backend/scripts/import_traders_detailed.py` - Python导入脚本
- `backend/scripts/generate_traders_sql.py` - SQL脚本生成器
- `backend/scripts/import_traders.sql` - 简化SQL脚本（仅游资主体）
- `backend/scripts/import_traders_complete.sql` - 完整SQL脚本（需生成）
