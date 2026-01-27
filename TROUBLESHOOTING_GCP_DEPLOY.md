# Google Cloud 部署故障排查指南

## 🔍 常见失败原因

### 1. 缺少必需的 GitHub Secrets（最常见）

**错误信息**：
- `Error: Missing required input: credentials_json`
- `Error: GCP_PROJECT_ID is not set`
- `Permission denied` 或 `Authentication failed`

**解决方案**：

访问 GitHub Secrets 页面：
```
https://github.com/flyingCloudRain/tradeview/settings/secrets/actions
```

确保已配置以下 **必需的** Secrets：

#### ✅ 必需配置

1. **GCP_PROJECT_ID**
   - 值：`tradeview-484009`

2. **GCP_SA_KEY**
   - 值：复制 `gcp-sa-key.json` 文件的完整 JSON 内容
   - 格式：完整的 JSON 对象，包括所有字段

#### 📋 可选配置（推荐）

3. **GCP_REGION**
   - 值：`us-central1`（默认值）

4. **FUNCTION_NAME**
   - 值：`trading-api`（默认值）

5. **FRONTEND_SERVICE_NAME**
   - 值：`trading-frontend`（默认值）

6. **DATABASE_URL**（如果使用数据库迁移）
   - 值：`postgresql://postgres:password@db.xxx.supabase.co:5432/postgres`

7. **SUPABASE_URL**（如果使用 Supabase）
   - 值：`https://xxx.supabase.co`

8. **CORS_ORIGINS**（前端部署后更新）
   - 值：`["https://your-frontend-domain.com"]`

### 2. GCP API 未启用

**错误信息**：
- `API cloudfunctions.googleapis.com is not enabled`
- `API cloudbuild.googleapis.com is not enabled`

**解决方案**：

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage-api.googleapis.com
```

或访问 [Google Cloud Console API Library](https://console.cloud.google.com/apis/library) 手动启用。

### 3. 服务账号权限不足

**错误信息**：
- `Permission denied`
- `The caller does not have permission`
- `PERMISSION_DENIED: Build failed because the default service account is missing required IAM permissions`
- `Caller does not have required permission to use project`

**解决方案**：

#### 3.1 GitHub Actions 服务账号权限

确保服务账号 `github-actions-deployer@YOUR_PROJECT.iam.gserviceaccount.com` 具有以下角色：

```bash
# 替换 YOUR_PROJECT 为实际项目 ID
PROJECT_ID="YOUR_PROJECT"
SA_EMAIL="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# 授予必要的角色
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudfunctions.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/cloudbuild.builds.builder"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/serviceusage.serviceUsageConsumer"
```

#### 3.2 Cloud Build 服务账号权限（重要！）

Cloud Build 默认服务账号也需要权限。获取项目编号并授予权限：

```bash
PROJECT_ID="YOUR_PROJECT"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "Cloud Build 服务账号: $CLOUD_BUILD_SA"

# 授予必要的角色
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/serviceusage.serviceUsageConsumer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUD_BUILD_SA}" \
  --role="roles/storage.admin"
```

**或者通过 GCP 控制台**：

1. 访问 [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. 找到 Cloud Build 服务账号：`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`
3. 点击编辑，添加以下角色：
   - `Service Usage Consumer` (roles/serviceusage.serviceUsageConsumer)
   - `Cloud Run Admin` (roles/run.admin)
   - `Service Account User` (roles/iam.serviceAccountUser)
   - `Storage Admin` (roles/storage.admin)

检查权限：
```bash
gcloud projects get-iam-policy tradeview-484009 \
  --flatten="bindings[].members" \
  --filter="bindings.members:github-actions-deployer@tradeview-484009.iam.gserviceaccount.com"
```

### 4. 入口点函数不存在

**错误信息**：
- `Entry point 'main' not found`
- `Function main is not defined`

**解决方案**：

确保 `backend/main.py` 中存在 `main` 函数。当前配置使用：
- 入口点：`main`
- 文件：`backend/main.py`

### 5. 依赖安装失败

**错误信息**：
- `ModuleNotFoundError`
- `pip install failed`

**解决方案**：

确保 `backend/requirements.txt` 包含所有必需的依赖，特别是：
- `mangum` 或 `functions-framework`（用于 Cloud Functions）
- `fastapi`
- `uvicorn`

## 🔧 快速修复步骤

### 步骤 1: 检查 GitHub Secrets

1. 访问：`https://github.com/flyingCloudRain/tradeview/settings/secrets/actions`
2. 确认以下 Secrets 存在：
   - ✅ `GCP_PROJECT_ID`
   - ✅ `GCP_SA_KEY`

### 步骤 2: 验证密钥文件

本地检查密钥文件：
```bash
cat gcp-sa-key.json
```

确保文件包含完整的 JSON，格式正确。

### 步骤 3: 检查 GCP 配置

```bash
# 设置项目
gcloud config set project tradeview-484009

# 检查 API 是否启用
gcloud services list --enabled | grep -E "cloudfunctions|cloudbuild|run"

# 检查服务账号
gcloud iam service-accounts list | grep github-actions-deployer
```

### 步骤 4: 重新运行工作流

1. 访问 GitHub Actions 页面
2. 选择失败的工作流运行
3. 点击 "Re-run all jobs" 或 "Re-run failed jobs"

## 📊 查看详细错误日志

1. 访问：`https://github.com/flyingCloudRain/tradeview/actions`
2. 点击失败的工作流运行
3. 展开失败的步骤
4. 查看错误日志

## 🆘 获取帮助

如果问题仍然存在：

1. **检查工作流日志**：查看具体的错误信息
2. **验证本地部署**：尝试使用 `deploy_gcp.sh` 脚本本地部署
3. **检查 GCP Console**：查看 Cloud Functions 和 Cloud Run 的状态

## ✅ 验证部署成功

部署成功后，你应该能够：

1. 在 GitHub Actions 中看到绿色的成功标记
2. 在 Google Cloud Console 中看到 Cloud Function 和 Cloud Run 服务
3. 访问部署的 URL（在工作流输出中显示）
