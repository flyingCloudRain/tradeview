# Google Cloud Functions 部署指南

## 概述

本指南介绍如何将交易复盘系统部署到 Google Cloud Functions。

## 架构

- **后端**: Google Cloud Functions (Gen 2) - Python 3.11
- **前端**: Google Cloud Storage (静态网站托管)
- **数据库**: Supabase (PostgreSQL)

## 前置条件

### 1. 安装 Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# 或访问: https://cloud.google.com/sdk/docs/install
```

### 2. 登录 Google Cloud

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. 创建项目（如果还没有）

```bash
# 创建项目
gcloud projects create your-project-id --name="Trading Review"

# 设置项目
gcloud config set project your-project-id

# 启用必要的 API
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage-api.googleapis.com
```

### 4. 配置环境变量

创建 `backend/.env` 文件或设置环境变量：

```bash
export DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
export SUPABASE_URL="https://xxx.supabase.co"
export SUPABASE_KEY="your-supabase-key"
export CORS_ORIGINS='["https://your-domain.com"]'
```

## 部署步骤

### 方式一：使用部署脚本（推荐）

```bash
# 设置项目 ID
export GCP_PROJECT="your-project-id"
export GCP_REGION="us-central1"  # 可选，默认 us-central1

# 执行部署
./deploy_gcp.sh
```

### 方式二：手动部署

#### 1. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 2. 运行数据库迁移（可选）

```bash
cd backend
python3 scripts/migrate_to_cloudbase.py
cd ..
```

#### 3. 部署 Cloud Function

```bash
cd backend

gcloud functions deploy trading-api \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=cloud_function \
    --trigger=http \
    --allow-unauthenticated \
    --memory=512MB \
    --timeout=540s \
    --max-instances=10 \
    --set-env-vars="DATABASE_URL=postgresql://...,SUPABASE_URL=https://..."
```

#### 4. 部署前端（可选）

```bash
# 创建存储桶
gsutil mb -p your-project-id -l us-central1 gs://your-project-id-frontend

# 设置网站托管
gsutil web set -m index.html -e index.html gs://your-project-id-frontend

# 上传文件
gsutil -m rsync -r -d frontend/dist gs://your-project-id-frontend
```

## 配置说明

### Cloud Function 配置

| 参数 | 值 | 说明 |
|------|-----|------|
| runtime | python311 | Python 3.11 运行时 |
| memory | 512MB | 内存大小（可调整） |
| timeout | 540s | 超时时间（最大 540s） |
| max-instances | 10 | 最大实例数 |
| trigger | http | HTTP 触发器 |

### 环境变量

在部署时通过 `--set-env-vars` 设置：

```bash
--set-env-vars="DATABASE_URL=...,SUPABASE_URL=...,CORS_ORIGINS=[\"https://...\"]"
```

或使用 Secret Manager（推荐用于生产环境）：

```bash
# 创建 Secret
echo -n "your-database-url" | gcloud secrets create database-url --data-file=-

# 在部署时引用
gcloud functions deploy trading-api \
    --gen2 \
    --update-secrets="DATABASE_URL=database-url:latest" \
    ...
```

## 获取函数 URL

部署完成后，获取函数 URL：

```bash
gcloud functions describe trading-api \
    --gen2 \
    --region=us-central1 \
    --format="value(serviceConfig.uri)"
```

输出示例：
```
https://trading-api-xxxxx-uc.a.run.app
```

## 更新前端配置

更新 `frontend/.env.production`：

```env
VITE_API_BASE_URL=https://trading-api-xxxxx-uc.a.run.app/api/v1
```

## 监控和日志

### 查看日志

```bash
gcloud functions logs read trading-api --gen2 --region=us-central1
```

### 监控指标

在 Google Cloud Console 中查看：
- 函数调用次数
- 错误率
- 延迟
- 内存使用

## 成本优化

1. **设置最小实例数**: 减少冷启动
   ```bash
   --min-instances=1
   ```

2. **调整内存**: 根据实际使用情况调整
   ```bash
   --memory=256MB  # 如果不需要太多内存
   ```

3. **设置并发数**: 控制同时处理的请求数
   ```bash
   --concurrency=80
   ```

## 故障排查

### 问题 1: 部署失败

**错误**: `Permission denied`

**解决方案**:
```bash
# 确保已启用必要的 API
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 问题 2: 函数无法访问数据库

**错误**: `Connection refused`

**解决方案**:
1. 检查环境变量是否正确设置
2. 检查数据库是否允许 Cloud Functions IP 访问
3. 使用 Secret Manager 存储敏感信息

### 问题 3: CORS 错误

**解决方案**:
1. 检查 `CORS_ORIGINS` 环境变量
2. 确保前端域名在允许列表中
3. 检查 `app/main.py` 中的 CORS 配置

## 与 CloudBase 的对比

| 特性 | CloudBase | Google Cloud Functions |
|------|-----------|------------------------|
| 运行时 | Python 3.9 | Python 3.11 |
| 最大超时 | 60s | 540s |
| 内存 | 512MB | 可配置 (128MB-8GB) |
| 冷启动 | 较快 | 较慢（Gen 2 改善） |
| 成本 | 按调用计费 | 按调用+内存+时间计费 |
| 区域 | 中国 | 全球 |

## 迁移检查清单

- [ ] 安装 Google Cloud SDK
- [ ] 创建 Google Cloud 项目
- [ ] 启用必要的 API
- [ ] 配置环境变量
- [ ] 运行数据库迁移
- [ ] 部署 Cloud Function
- [ ] 更新前端 API URL
- [ ] 测试 API 端点
- [ ] 配置监控和告警

## 相关文档

- [Google Cloud Functions 文档](https://cloud.google.com/functions/docs)
- [FastAPI 部署指南](https://fastapi.tiangolo.com/deployment/)
- `deploy_gcp.sh` - 部署脚本
- `backend/main.py` - Cloud Functions 入口文件
