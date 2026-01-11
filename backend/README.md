# 交易复盘系统 - 后端

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置数据库连接：

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/trading_review
```

### 3. 初始化数据库

**方式一：使用Python脚本（推荐）**

```bash
python scripts/init_database.py
```

**方式二：使用Alembic迁移**

```bash
# 创建初始迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

**方式三：使用SQL脚本**

```bash
psql $DATABASE_URL -f scripts/create_tables.sql
```

### 4. 验证数据库

```bash
python scripts/verify_database.py
```

### 5. 运行应用

```bash
uvicorn app.main:app --reload --port 8000
```

### 6. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

> 📖 详细的数据库初始化说明请查看 [DATABASE_INIT.md](DATABASE_INIT.md)

## 项目结构

```
backend/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── api/                 # API路由
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic模式
│   ├── services/            # 业务逻辑层
│   ├── database/            # 数据库相关
│   └── utils/               # 工具函数
└── requirements.txt
```

## API端点

- `/api/v1/lhb` - 龙虎榜
- `/api/v1/zt-pool` - 涨停池
- `/api/v1/index` - 大盘指数
- `/api/v1/sector` - 概念板块
- `/api/v1/stock-fund-flow` - 个股资金流
- `/api/v1/capital` - 活跃机构

