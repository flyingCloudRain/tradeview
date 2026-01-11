# GitHub Actions Workflows

## 自动部署到 Google Cloud Platform

### 快速开始

1. **配置 GitHub Secrets**
   - 访问仓库设置：`Settings` → `Secrets and variables` → `Actions`
   - 添加必需的 Secrets（见下方）

2. **推送代码到 main 分支**
   ```bash
   git add .
   git commit -m "Setup auto deployment"
   git push origin main
   ```

3. **查看部署状态**
   - 访问 GitHub 仓库的 `Actions` 标签页
   - 查看 workflow 运行状态

### 必需的 GitHub Secrets

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `GCP_PROJECT_ID` | Google Cloud 项目 ID | `my-trading-project` |
| `GCP_SA_KEY` | 服务账号 JSON 密钥（完整内容） | `{"type":"service_account",...}` |

### 可选的 GitHub Secrets

| Secret 名称 | 说明 | 默认值 |
|------------|------|--------|
| `GCP_REGION` | GCP 区域 | `us-central1` |
| `FUNCTION_NAME` | Cloud Function 名称 | `trading-api` |
| `FRONTEND_SERVICE_NAME` | Cloud Run 服务名称 | `trading-frontend` |
| `DATABASE_URL` | 数据库连接字符串 | - |
| `SUPABASE_URL` | Supabase 项目 URL | - |
| `SUPABASE_KEY` | Supabase API Key | - |
| `SUPABASE_SERVICE_KEY` | Supabase Service Key | - |
| `CORS_ORIGINS` | CORS 允许的前端 URL | - |

### 触发方式

#### 自动触发
- 推送到 `main` 或 `master` 分支时自动触发

#### 手动触发
1. 访问 GitHub 仓库的 `Actions` 标签页
2. 选择 `Deploy to Google Cloud Platform` workflow
3. 点击 `Run workflow`
4. 选择要部署的组件（后端/前端）
5. 点击 `Run workflow` 按钮

### 部署流程

1. **后端部署** (`deploy-backend`)
   - 安装 Python 依赖
   - 运行数据库迁移（如果配置了 `DATABASE_URL`）
   - 部署到 Cloud Functions (Gen 2)
   - 获取并显示 API URL

2. **前端部署** (`deploy-frontend`)
   - 安装 Node.js 依赖
   - 获取后端 API URL
   - 构建前端（自动设置 API URL）
   - 部署到 Cloud Run
   - 获取并显示前端 URL

### 故障排查

#### 认证失败
- 检查 `GCP_SA_KEY` Secret 是否正确（完整 JSON 内容）
- 确认服务账号有必要的权限

#### API 未启用
```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com
```

#### 部署超时
- Cloud Functions 部署可能需要 5-10 分钟
- 检查 GCP 控制台是否有错误

### 相关文档

- [完整配置指南](../AUTO_DEPLOY_GCP.md)
- [GitHub Actions 设置指南](../GITHUB_ACTIONS_SETUP.md)
- [Google Cloud 部署文档](../GOOGLE_CLOUD_DEPLOY.md)
