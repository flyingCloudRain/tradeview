# 修复 Cloud Run 部署权限问题

## 问题描述

部署时出现错误：
```
PERMISSION_DENIED: Build failed because the default service account is missing required IAM permissions.
Caller does not have required permission to use project ***.
```

## 快速修复（推荐）

### 方法一：使用 gcloud 命令（需要项目所有者权限）

```bash
# 设置项目 ID
export PROJECT_ID="your-project-id"  # 替换为实际项目 ID
gcloud config set project $PROJECT_ID

# 获取项目编号
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

echo "✅ 权限授予完成"
```

### 方法二：通过 GCP 控制台

1. 访问 [IAM & Admin](https://console.cloud.google.com/iam-admin/iam)
2. 选择你的项目
3. 找到 Cloud Build 服务账号（格式：`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`）
   - 如果找不到，点击 "Grant Access" 添加
   - 服务账号邮箱格式：`数字@cloudbuild.gserviceaccount.com`
4. 点击编辑（铅笔图标）
5. 添加以下角色：
   - ✅ **Service Usage Consumer** (`roles/serviceusage.serviceUsageConsumer`)
   - ✅ **Cloud Run Admin** (`roles/run.admin`)
   - ✅ **Service Account User** (`roles/iam.serviceAccountUser`)
   - ✅ **Storage Admin** (`roles/storage.admin`)
6. 保存更改

### 方法三：使用更新后的设置脚本

运行更新后的设置脚本，它会自动授予所有必要的权限：

```bash
./scripts/setup_gcp_service_account.sh
```

## 验证权限

授予权限后，验证是否成功：

```bash
PROJECT_ID="your-project-id"
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:${CLOUD_BUILD_SA}" \
  --format="table(bindings.role)"
```

## 重新部署

权限授予后（可能需要几分钟生效），重新运行 GitHub Actions 工作流：

1. 访问 GitHub Actions 页面
2. 选择最新的工作流运行
3. 点击 "Re-run all jobs"

## 注意事项

- 权限更改可能需要几分钟才能生效
- 确保使用项目所有者或有足够权限的账号执行权限授予操作
- Cloud Build 服务账号的邮箱格式：`PROJECT_NUMBER@cloudbuild.gserviceaccount.com`
