# 🔧 快速修复 Google Cloud 部署失败

## 问题诊断

工作流失败最可能的原因是 **缺少必需的 GitHub Secrets**。

## ✅ 立即修复步骤

### 步骤 1: 配置 GitHub Secrets（必需）

访问 GitHub Secrets 页面：
```
https://github.com/flyingCloudRain/tradeview/settings/secrets/actions
```

#### Secret 1: GCP_PROJECT_ID

1. 点击 **"New repository secret"**
2. Name: `GCP_PROJECT_ID`
3. Secret: `tradeview-484009`
4. 点击 **"Add secret"**

#### Secret 2: GCP_SA_KEY

1. 点击 **"New repository secret"**
2. Name: `GCP_SA_KEY`
3. Secret: 复制 `gcp-sa-key.json` 文件的完整 JSON 内容

**⚠️ 重要**：
- 文件位置：项目根目录的 `gcp-sa-key.json`
- 必须复制完整的 JSON，包括所有字段和换行符
- 不要修改任何内容，直接复制粘贴整个文件内容

### 步骤 2: 验证配置

配置完成后：

1. 访问 Actions 页面：`https://github.com/flyingCloudRain/tradeview/actions`
2. 找到失败的工作流运行
3. 点击 **"Re-run all jobs"** 或推送新的提交触发部署

### 步骤 3: 检查 GCP API（如果仍然失败）

如果配置了 Secrets 仍然失败，检查 GCP API 是否已启用：

```bash
# 设置项目
gcloud config set project tradeview-484009

# 启用必需的 API
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage-api.googleapis.com
```

## 📊 验证部署

部署成功后，你应该能够：

1. ✅ 在 GitHub Actions 中看到绿色的成功标记
2. ✅ 在 [Google Cloud Console](https://console.cloud.google.com/functions) 中看到 Cloud Function
3. ✅ 在工作流输出中看到部署的 URL

## 🆘 仍然失败？

查看详细错误日志：
1. 访问：`https://github.com/flyingCloudRain/tradeview/actions`
2. 点击失败的工作流运行
3. 展开失败的步骤查看错误信息

参考完整故障排查指南：`TROUBLESHOOTING_GCP_DEPLOY.md`
