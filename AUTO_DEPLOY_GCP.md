# GCP 自动部署配置指南

本文档介绍如何配置 GitHub Actions 自动部署到 Google Cloud Platform (GCP)。

## 概述

配置完成后，每次推送到 `main` 或 `master` 分支时，系统会自动：
1. 运行数据库迁移
2. 部署后端到 Google Cloud Functions (Gen 2)
3. 构建并部署前端到 Cloud Run
4. 自动更新前端 API URL 配置

## 前置条件

### 1. 创建 Google Cloud 服务账号

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 进入 **IAM & Admin** → **Service Accounts**
3. 点击 **Create Service Account**
4. 填写服务账号信息：
   - **Name**: `github-actions-deployer`
   - **Description**: `Service account for GitHub Actions deployment`
5. 授予以下角色：
   - `Cloud Functions Admin`
   - `Cloud Run Admin`
   - `Storage Admin`
   - `Service Account User`
   - `Cloud Build Service Account`
6. 创建并下载 JSON 密钥文件

### 2. 配置 GitHub Secrets

访问 GitHub 仓库：**Settings** → **Secrets and variables** → **Actions**

点击 **New repository secret** 添加以下 Secrets：

#### 必需 Secrets

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `GCP_PROJECT_ID` | GCP 项目 ID | Google Cloud Console → 项目选择器 |
| `GCP_SA_KEY` | 服务账号 JSON 密钥 | 下载的服务账号密钥文件内容（完整 JSON） |

#### 可选但推荐的 Secrets

| Secret 名称 | 说明 | 格式示例 |
|------------|------|---------|
| `GCP_REGION` | GCP 区域（默认：us-central1） | `us-central1` |
| `FUNCTION_NAME` | Cloud Function 名称（默认：trading-api） | `trading-api` |
| `FRONTEND_SERVICE_NAME` | Cloud Run 服务名称（默认：trading-frontend） | `trading-frontend` |
| `DATABASE_URL` | 数据库连接字符串 | `postgresql://user:pass@host:5432/db` |
| `SUPABASE_URL` | Supabase 项目 URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase API Key | `eyJhbGc...` |
| `SUPABASE_SERVICE_KEY` | Supabase Service Key | `eyJhbGc...` |
| `CORS_ORIGINS` | CORS 允许的前端 URL | `["https://example.com"]` |

### 3. 获取 GCP 项目 ID

```bash
# 如果已安装 gcloud CLI
gcloud config get-value project

# 或在 Google Cloud Console 中查看
# 项目选择器显示的项目 ID
```

### 4. 创建服务账号密钥

**方式一：使用自动化脚本（推荐）**

```bash
# 设置项目 ID
export GCP_PROJECT=your-project-id

# 运行设置脚本
./scripts/setup_gcp_service_account.sh
```

**方式二：手动创建**

```bash
# 使用 gcloud CLI 创建密钥
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com

# 复制 key.json 的内容作为 GCP_SA_KEY Secret
```

**注意**：如果遇到权限错误，请确保：
1. 已正确设置项目 ID
2. 服务账号邮箱格式正确：`github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com`
3. 使用正确的角色名称（完整路径，如 `roles/cloudfunctions.admin`）

## 配置步骤

### 步骤 1: 添加 GitHub Secrets

1. 进入 GitHub 仓库设置页面
2. 导航到 **Secrets and variables** → **Actions**
3. 添加以下 Secrets：

#### 最小配置（必需）

```
GCP_PROJECT_ID=your-project-id
GCP_SA_KEY={"type":"service_account","project_id":"..."}
```

#### 完整配置（推荐）

```
GCP_PROJECT_ID=your-project-id
GCP_SA_KEY={"type":"service_account",...}
GCP_REGION=us-central1
FUNCTION_NAME=trading-api
FRONTEND_SERVICE_NAME=trading-frontend
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-supabase-key
SUPABASE_SERVICE_KEY=your-service-key
CORS_ORIGINS=["https://your-frontend-domain.com"]
```

### 步骤 2: 启用必要的 GCP API

确保以下 API 已启用：

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage-api.googleapis.com \
  artifactregistry.googleapis.com
```

或在 [Google Cloud Console](https://console.cloud.google.com/apis/library) 中手动启用。

### 步骤 3: 测试部署

1. 推送代码到 `main` 分支：
   ```bash
   git push origin main
   ```

2. 查看部署状态：
   - 访问 GitHub 仓库的 **Actions** 标签页
   - 查看最新的 workflow 运行状态

3. 验证部署：
   - 后端：检查 Cloud Functions 是否部署成功
   - 前端：访问 Cloud Run 服务 URL

## Workflow 说明

### 触发条件

- **自动触发**：推送到 `main` 或 `master` 分支
- **手动触发**：在 Actions 页面点击 "Run workflow"

### 部署流程

1. **后端部署** (`deploy-backend` job):
   - 安装 Python 依赖
   - 运行数据库迁移（如果配置了 `DATABASE_URL`）
   - 部署到 Cloud Functions (Gen 2)
   - 获取并显示 API URL

2. **前端部署** (`deploy-frontend` job):
   - 安装 Node.js 依赖
   - 获取后端 API URL
   - 构建前端（自动设置 API URL）
   - 部署到 Cloud Run
   - 获取并显示前端 URL

3. **部署摘要** (`deployment-complete` job):
   - 显示部署状态和 URL

## 环境变量配置

### 后端环境变量

在部署时通过 `--set-env-vars` 设置，包括：
- `DATABASE_URL`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `CORS_ORIGINS`

### 前端环境变量

在构建时通过 `.env.production` 设置：
- `VITE_API_BASE_URL`：自动从后端部署获取

## 手动触发部署

1. 访问 GitHub 仓库的 **Actions** 标签页
2. 选择 **Deploy to Google Cloud Platform** workflow
3. 点击 **Run workflow**
4. 选择要部署的组件：
   - ✅ Deploy Backend
   - ✅ Deploy Frontend
5. 点击 **Run workflow** 按钮

## 故障排查

### 问题 1: 认证失败

**错误**: `Permission denied` 或 `Authentication error`

**解决方案**:
1. 检查 `GCP_SA_KEY` Secret 是否正确（完整 JSON 内容）
2. 确认服务账号有必要的权限
3. 验证项目 ID 是否正确

### 问题 2: API 未启用

**错误**: `API not enabled`

**解决方案**:
```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
```

### 问题 3: 数据库迁移失败

**错误**: `Database migration failed`

**解决方案**:
1. 检查 `DATABASE_URL` Secret 格式是否正确
2. 确认数据库允许 Cloud Functions IP 访问
3. 查看 workflow 日志获取详细错误信息

### 问题 4: 前端构建失败

**错误**: `Build failed`

**解决方案**:
1. 检查前端代码是否有语法错误
2. 确认 `package.json` 依赖正确
3. 查看构建日志定位问题

### 问题 5: 部署超时

**错误**: `Deployment timeout`

**解决方案**:
1. Cloud Functions 部署可能需要较长时间（5-10 分钟）
2. 检查 GCP 控制台是否有错误
3. 增加 workflow 超时时间（在 workflow 文件中）

## 最佳实践

1. **使用 Secret Manager**（生产环境推荐）:
   ```bash
   # 创建 Secret
   echo -n "your-secret-value" | gcloud secrets create secret-name --data-file=-
   
   # 在部署时引用
   --update-secrets="ENV_VAR=secret-name:latest"
   ```

2. **分支保护**:
   - 只允许从 `main` 分支部署
   - 要求代码审查
   - 要求通过 CI 检查

3. **监控和告警**:
   - 配置 Cloud Monitoring 告警
   - 设置部署失败通知

4. **回滚机制**:
   - 保留之前的部署版本
   - 准备快速回滚脚本

5. **测试环境**:
   - 创建独立的测试环境
   - 使用不同的 GCP 项目或区域

## 成本优化

1. **设置最小实例数**:
   ```yaml
   --min-instances=0  # 允许冷启动
   ```

2. **调整资源限制**:
   ```yaml
   --memory=256MB  # 根据实际需求调整
   --max-instances=5  # 限制最大实例数
   ```

3. **使用 Cloud Run 计费**:
   - Cloud Run 按请求计费，更经济
   - 考虑将后端也迁移到 Cloud Run

## 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Google Cloud Functions 文档](https://cloud.google.com/functions/docs)
- [Cloud Run 文档](https://cloud.google.com/run/docs)
- [GitHub Actions for GCP](https://github.com/google-github-actions)

## 下一步

1. ✅ 配置 GitHub Secrets
2. ✅ 启用必要的 GCP API
3. ✅ 推送代码测试部署
4. ✅ 验证部署结果
5. ✅ 配置监控和告警

## 示例：完整的 Secret 配置

```bash
# 在 GitHub Secrets 中配置

GCP_PROJECT_ID=my-trading-project
GCP_REGION=us-central1
FUNCTION_NAME=trading-api
FRONTEND_SERVICE_NAME=trading-frontend

# GCP_SA_KEY (完整 JSON)
{
  "type": "service_account",
  "project_id": "my-trading-project",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "github-actions-deployer@my-trading-project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}

DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
CORS_ORIGINS=["https://trading-frontend-xxx-uc.a.run.app"]
```
