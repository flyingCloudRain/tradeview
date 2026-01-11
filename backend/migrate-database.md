# Supabase 数据库迁移指南

## 概述

如果使用 Supabase（PostgreSQL）数据库，**必须运行 Alembic 迁移**来创建数据库表结构。

## 迁移步骤

### 1. 配置数据库连接

确保环境变量中配置了 Supabase 数据库连接：

```bash
# Supabase 数据库连接字符串格式
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres
```

### 2. 运行迁移

#### 方式一：本地运行（推荐用于首次迁移）

```bash
cd backend

# 设置环境变量
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# 运行所有迁移
alembic upgrade head
```

#### 方式二：使用初始化脚本

```bash
cd backend
bash scripts/init_database.sh
# 选择选项 2（使用Alembic迁移）
```

### 3. 验证迁移

```bash
cd backend
python scripts/verify_database.py
```

## CloudBase 部署时的迁移

### 方案一：部署前本地迁移（推荐）

在部署到 CloudBase 之前，先在本地运行迁移：

```bash
# 1. 配置 Supabase 数据库连接
export DATABASE_URL="your-supabase-connection-string"

# 2. 运行迁移
cd backend
alembic upgrade head

# 3. 验证迁移成功
python scripts/verify_database.py
```

### 方案二：云函数启动时自动迁移

修改 `backend/index.py`，在云函数启动时自动运行迁移：

```python
"""
CloudBase 云函数入口
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from app.main import app

def main_handler(event, context):
    """
    云函数入口
    """
    # 首次启动时运行迁移（可选）
    # 注意：这会在每次冷启动时运行，可能影响性能
    # 建议在部署前手动运行迁移
    # try:
    #     from alembic.config import Config
    #     from alembic import command
    #     alembic_cfg = Config("alembic.ini")
    #     command.upgrade(alembic_cfg, "head")
    # except Exception as e:
    #     print(f"Migration error: {e}")
    
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
    return handler(event, context)
```

### 方案三：创建独立的迁移云函数

创建一个专门用于数据库迁移的云函数：

1. 在 `backend/cloudbase.json` 中添加迁移函数配置
2. 创建 `backend/migrate.py` 作为迁移函数入口
3. 需要时手动触发迁移函数

## 迁移文件说明

项目包含以下迁移文件（按执行顺序）：

1. `add_trading_calendar.py` - 交易日历表
2. `add_trader_and_branch.py` - 交易员和分支表
3. `add_task_execution_table.py` - 任务执行表
4. `add_price_and_is_executed_to_trading_calendar.py` - 交易日历字段扩展
5. ... 以及其他迁移文件

## 注意事项

1. **首次部署必须运行迁移**：Supabase 数据库是空的，需要运行所有迁移创建表结构
2. **迁移顺序很重要**：Alembic 会自动按顺序执行迁移
3. **数据备份**：在生产环境运行迁移前，建议备份数据库
4. **回滚**：如果需要回滚，使用 `alembic downgrade -1` 或指定版本号

## 检查迁移状态

```bash
# 查看当前数据库版本
alembic current

# 查看迁移历史
alembic history

# 查看待执行的迁移
alembic heads
```

## 常见问题

### Q1: 迁移失败怎么办？
A: 检查数据库连接字符串是否正确，确保 Supabase 数据库允许连接。

### Q2: 如何跳过某些迁移？
A: 不推荐跳过，但可以使用 `alembic stamp <revision>` 标记某个版本。

### Q3: 迁移后数据丢失？
A: 迁移只会创建/修改表结构，不会删除数据。但建议先备份。

### Q4: 在 CloudBase 中如何运行迁移？
A: 推荐在部署前本地运行迁移，或创建独立的迁移云函数。
