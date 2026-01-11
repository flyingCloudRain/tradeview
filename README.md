# 交易复盘系统

前后端分离的交易复盘系统，提供全面的A股市场数据分析功能。

## 技术栈

### 前端
- Vue 3 + TypeScript
- Vite
- Element Plus
- Pinia
- Vue Router 4
- ECharts

### 后端
- FastAPI (Python 3.11+)
- SQLAlchemy 2.0
- Supabase (PostgreSQL)
- AKShare

## 快速开始

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 功能模块

- 📊 龙虎榜查询与分析
- 💰 活跃机构（游资）查询与分析
- 📈 每日大盘指数监控
- 🏢 概念板块上涨情况分析
- 💸 个股资金流分析
- 🚀 涨停个股分析

## 项目结构

```
trading_review_new/
├── backend/          # 后端项目
├── frontend/         # 前端项目
├── docs/             # 文档
└── DESIGN.md         # 设计方案
```

## 开发计划

详见 `DESIGN.md` 文件。
