# 配置环境说明

## 问题描述

应用同时存在本地开发配置和 GCP 云环境配置，可能导致配置冲突。

## 配置优先级

### 本地开发环境

1. **环境变量**（最高优先级）
2. **`.env` 文件**（如果存在）
3. **默认值**

### GCP 云环境（Cloud Functions Gen 2）

1. **环境变量**（唯一来源）
2. **`.env` 文件被禁用**（不会加载）

## 已实施的修复

### 1. 代码层面

在 `backend/app/config.py` 中：

```python
class Config:
    # 在 GCP 环境中，不使用 .env 文件，只使用环境变量
    is_gcp = os.getenv("FUNCTION_TARGET") or os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT")
    env_file = None if is_gcp else ".env"  # GCP 环境中禁用 .env 文件
    case_sensitive = True
```

### 2. 部署层面

在 `backend/.gcloudignore` 中：

```
# Environment
.env
.env.local
.env.*.local
```

确保 `.env` 文件不会被部署到 GCP。

## 环境检测

应用通过以下环境变量检测是否在 GCP 环境中：

- `FUNCTION_TARGET` - Cloud Functions Gen 2
- `K_SERVICE` - Cloud Run
- `GOOGLE_CLOUD_PROJECT` - GCP 项目

## 配置来源

### 本地开发

创建 `backend/.env` 文件：

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-key
LOG_LEVEL=INFO
```

### GCP 部署

通过 GitHub Secrets 或 gcloud 命令设置环境变量：

```bash
# 通过 gcloud 设置
gcloud functions deploy trading-api \
  --gen2 \
  --region=us-central1 \
  --set-env-vars "DATABASE_URL=...,SUPABASE_URL=..."
```

或通过 GitHub Secrets：
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `CORS_ORIGINS`

## 验证配置

### 检查当前环境

```python
import os

is_gcp = os.getenv("FUNCTION_TARGET") or os.getenv("K_SERVICE") or os.getenv("GOOGLE_CLOUD_PROJECT")
print(f"GCP 环境: {is_gcp}")
print(f"使用 .env 文件: {not is_gcp}")
```

### 查看实际使用的配置

在应用启动时查看日志：

```bash
# 本地开发
python backend/main.py

# GCP 环境
gcloud functions logs read trading-api --gen2 --region=us-central1 --limit=20
```

## 常见问题

### Q: 为什么 GCP 环境中不使用 .env 文件？

A: 为了安全性和一致性：
- 避免敏感信息被提交到代码仓库
- 确保使用 GCP 环境变量，而不是本地配置
- 防止配置冲突

### Q: 如何在不同环境使用不同配置？

A: 使用环境变量：
- 本地：`.env` 文件
- GCP：Cloud Functions 环境变量
- 代码自动检测环境并选择正确的配置源

### Q: 如果配置加载失败怎么办？

A: 应用有容错机制：
- 如果配置加载失败，会使用 `MinimalSettings`
- 数据库连接会延迟初始化
- 健康检查端点不依赖数据库

## 最佳实践

1. ✅ **本地开发**：使用 `.env` 文件
2. ✅ **GCP 部署**：使用环境变量（GitHub Secrets）
3. ✅ **不要提交**：`.env` 文件到 Git
4. ✅ **确保排除**：`.gcloudignore` 中排除 `.env` 文件
