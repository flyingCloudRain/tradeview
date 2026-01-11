# 数据库配置更新为 Supabase

## 更新概述

本次更新将所有数据库配置统一为 Supabase PostgreSQL 数据库，移除了所有 SQLite 相关的代码和配置。

## 更新内容

### 1. 核心数据库配置

#### `backend/app/database/session.py`
- ✅ 移除了 SQLite 兼容代码
- ✅ 添加了数据库类型验证，仅支持 PostgreSQL/Supabase
- ✅ 简化了连接池配置，仅保留 PostgreSQL 配置
- ✅ 移除了 SQLite 相关的超时设置检查

**变更前：**
- 支持 SQLite 和 PostgreSQL 两种数据库
- 根据数据库类型动态选择连接参数

**变更后：**
- 仅支持 PostgreSQL/Supabase
- 如果 DATABASE_URL 不是 PostgreSQL 连接字符串，会抛出错误

#### `backend/app/config.py`
- ✅ 已要求必须设置 DATABASE_URL 环境变量
- ✅ 已包含 Supabase 相关配置（SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY）

### 2. 启动脚本

#### `backend/start_backend.sh`
- ✅ 移除了 SQLite 默认数据库配置
- ✅ 添加了 DATABASE_URL 环境变量检查
- ✅ 添加了数据库类型验证（必须是 PostgreSQL）
- ✅ 改进了错误提示信息

**变更前：**
```bash
if [ -z "$DATABASE_URL" ]; then
    export DATABASE_URL="sqlite:///$(pwd)/data/trading_review.db"
fi
```

**变更后：**
```bash
if [ -z "$DATABASE_URL" ]; then
    echo "❌ 错误: DATABASE_URL 环境变量未设置"
    exit 1
fi
```

### 3. 数据库迁移脚本

#### `backend/scripts/add_flag_column_to_lhb_institution.py`
- ✅ 移除了 SQLite fallback 逻辑
- ✅ 要求必须设置 DATABASE_URL 环境变量
- ✅ 添加了数据库类型验证
- ✅ 移除了 SQLite 特定的 ALTER TABLE 语法

#### `backend/scripts/add_concept_column_to_lhb_detail.py`
- ✅ 移除了 SQLite fallback 逻辑
- ✅ 要求必须设置 DATABASE_URL 环境变量
- ✅ 添加了数据库类型验证
- ✅ 移除了 SQLite 特定的 PRAGMA 查询

### 4. Alembic 迁移文件

#### `backend/alembic/versions/add_flag_column_to_lhb_institution.py`
- ✅ 移除了 SQLite 兼容代码
- ✅ 仅保留 PostgreSQL/Supabase 支持
- ✅ 添加了数据库类型验证

**变更前：**
- 支持 SQLite 和 PostgreSQL 两种数据库
- 使用 PRAGMA table_info 检查 SQLite 列

**变更后：**
- 仅支持 PostgreSQL/Supabase
- 使用 information_schema 检查列

### 5. 环境变量配置

#### `backend/setup_env.sh`
- ✅ 已配置 Supabase PostgreSQL 连接字符串
- ✅ 已配置 Supabase URL

## 使用说明

### 设置环境变量

在使用项目之前，必须设置 `DATABASE_URL` 环境变量：

```bash
# 方式1: 使用 setup_env.sh 脚本
source backend/setup_env.sh

# 方式2: 手动设置
export DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
export SUPABASE_URL="https://xxx.supabase.co"
```

### 启动后端服务

```bash
# 确保已设置 DATABASE_URL
cd backend
source setup_env.sh  # 或手动设置环境变量
./start_backend.sh
```

### 运行数据库迁移脚本

```bash
# 确保已设置 DATABASE_URL
export DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"

# 运行迁移脚本
PYTHONPATH=. python backend/scripts/add_flag_column_to_lhb_institution.py
PYTHONPATH=. python backend/scripts/add_concept_column_to_lhb_detail.py
```

## 验证清单

- [x] `backend/app/database/session.py` - 仅支持 PostgreSQL/Supabase
- [x] `backend/start_backend.sh` - 要求设置 DATABASE_URL
- [x] `backend/scripts/add_flag_column_to_lhb_institution.py` - 移除 SQLite 支持
- [x] `backend/scripts/add_concept_column_to_lhb_detail.py` - 移除 SQLite 支持
- [x] `backend/alembic/versions/add_flag_column_to_lhb_institution.py` - 移除 SQLite 支持
- [x] `backend/setup_env.sh` - 配置 Supabase 连接

## 注意事项

1. **必须设置 DATABASE_URL**: 所有脚本和应用程序现在都要求必须设置 `DATABASE_URL` 环境变量，不再提供 SQLite 默认值。

2. **仅支持 PostgreSQL**: 项目现在仅支持 PostgreSQL/Supabase 数据库，不再支持 SQLite。

3. **环境变量检查**: 启动脚本和迁移脚本都会检查 `DATABASE_URL` 是否设置，如果未设置会显示错误信息并退出。

4. **数据库类型验证**: 所有脚本都会验证 `DATABASE_URL` 是否为 PostgreSQL 连接字符串（以 `postgresql://` 开头）。

5. **向后兼容性**: Alembic 迁移文件已更新，移除了 SQLite 支持。如果之前使用 SQLite 数据库，需要先迁移到 Supabase。

## 迁移指南

如果您之前使用 SQLite 数据库，需要：

1. 在 Supabase 中创建新的 PostgreSQL 数据库
2. 使用 Alembic 或 SQL 脚本初始化数据库结构
3. 迁移数据（如果需要）
4. 更新 `DATABASE_URL` 环境变量指向 Supabase

## 相关文件

- `backend/app/config.py` - 应用配置
- `backend/app/database/session.py` - 数据库会话管理
- `backend/setup_env.sh` - 环境变量设置脚本
- `backend/start_backend.sh` - 后端启动脚本
- `backend/alembic/env.py` - Alembic 环境配置（已从 settings.DATABASE_URL 读取）
