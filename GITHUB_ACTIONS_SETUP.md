# GitHub Actions 自动部署快速设置指南

## 🚀 5分钟快速配置

### 步骤 1: 创建 GCP 服务账号（2分钟）

**方式一：使用自动化脚本（推荐）**

```bash
# 设置项目 ID（如果还没有）
export GCP_PROJECT=your-project-id
# 或
gcloud config set project your-project-id

# 运行设置脚本
./scripts/setup_gcp_service_account.sh
```

脚本会自动：
- 创建服务账号
- 授予所有必要的权限
- 创建并下载密钥文件
- 显示配置说明

**方式二：手动创建**

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 进入 **IAM & Admin** → **Service Accounts**
3. 点击 **Create Service Account**
4. 填写信息：
   - **Name**: `github-actions-deployer`
5. 授予角色：
   - `Cloud Functions Admin`
   - `Cloud Run Admin`
   - `Storage Admin`
   - `Service Account User`
   - `Cloud Build Service Account`
6. 创建并下载 JSON 密钥文件

### 步骤 2: 配置 GitHub Secrets（2分钟）

访问：`https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions`

添加以下 Secrets：

#### 最小配置（必需）

```
GCP_PROJECT_ID = your-project-id
GCP_SA_KEY = {粘贴完整的 JSON 密钥文件内容}
```

#### 完整配置（推荐）

```
GCP_PROJECT_ID = your-project-id
GCP_SA_KEY = {完整的 JSON 密钥}
GCP_REGION = us-central1
FUNCTION_NAME = trading-api
FRONTEND_SERVICE_NAME = trading-frontend
DATABASE_URL = postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
SUPABASE_URL = https://xxx.supabase.co
SUPABASE_KEY = your-key
SUPABASE_SERVICE_KEY = your-service-key
CORS_ORIGINS = ["https://your-frontend-domain.com"]
```

### 步骤 3: 启用 GCP API（1分钟）

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com
```

或在 [API Library](https://console.cloud.google.com/apis/library) 中手动启用。

### 步骤 4: 测试部署

推送代码到 `main` 分支：

```bash
git add .
git commit -m "Setup auto deployment"
git push origin main
```

查看部署状态：
- GitHub → Actions 标签页
- 查看 workflow 运行状态

## 📋 配置检查清单

- [ ] GCP 项目已创建
- [ ] 服务账号已创建并授予权限
- [ ] 服务账号密钥已下载
- [ ] GitHub Secrets 已配置（至少 `GCP_PROJECT_ID` 和 `GCP_SA_KEY`）
- [ ] 必要的 GCP API 已启用
- [ ] 代码已推送到 `main` 分支
- [ ] GitHub Actions workflow 运行成功

## 🔍 验证部署

部署成功后，获取服务 URL：

```bash
# 后端 API URL
gcloud functions describe trading-api \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.uri)"

# 前端 URL
gcloud run services describe trading-frontend \
  --region=us-central1 \
  --format="value(status.url)"
```

## 📚 详细文档

- [完整配置指南](./AUTO_DEPLOY_GCP.md)
- [GCP 部署文档](./GOOGLE_CLOUD_DEPLOY.md)

## ❓ 常见问题

### Q: 部署失败，提示权限错误？
A: 检查服务账号是否有必要的角色权限。

### Q: 如何查看详细的部署日志？
A: 在 GitHub Actions 页面点击对应的 workflow run，查看详细日志。

### Q: 可以只部署后端或前端吗？
A: 可以！在 Actions 页面手动触发 workflow，可以选择只部署后端或前端。

### Q: 如何回滚部署？
A: 使用 `gcloud functions deploy` 的 `--revision` 参数指定之前的版本。

## 🎯 下一步

1. ✅ 配置完成
2. ✅ 测试部署
3. 🔄 配置监控和告警
4. 🔄 设置分支保护规则
5. 🔄 配置自动测试
