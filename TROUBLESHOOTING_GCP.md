# GCP 部署故障排查指南

## 常见错误及解决方案

### 错误 1: `INVALID_ARGUMENT: Request contains an invalid argument`

**原因**：
- 服务账号邮箱格式不正确
- 项目 ID 格式不正确
- 角色名称不正确
- 命令语法错误

**解决方案**：

#### 方法 1: 使用自动化脚本（推荐）

```bash
# 设置项目 ID
export GCP_PROJECT=your-project-id

# 运行设置脚本
./scripts/setup_gcp_service_account.sh
```

#### 方法 2: 手动检查并修复

1. **检查项目 ID**：
   ```bash
   gcloud config get-value project
   ```

2. **检查服务账号邮箱格式**：
   ```bash
   # 正确的格式
   github-actions-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com
   
   # 检查服务账号是否存在
   gcloud iam service-accounts list
   ```

3. **使用正确的角色名称**：
   ```bash
   # ✅ 正确 - 使用完整角色路径
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/cloudfunctions.admin"
   
   # ❌ 错误 - 角色名称不完整
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com" \
     --role="Cloud Functions Admin"
   ```

4. **完整的正确命令示例**：
   ```bash
   # 设置变量
   PROJECT_ID="your-project-id"
   SA_EMAIL="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"
   
   # 授予权限（逐个执行）
   gcloud projects add-iam-policy-binding "$PROJECT_ID" \
     --member="serviceAccount:${SA_EMAIL}" \
     --role="roles/cloudfunctions.admin"
   
   gcloud projects add-iam-policy-binding "$PROJECT_ID" \
     --member="serviceAccount:${SA_EMAIL}" \
     --role="roles/run.admin"
   
   gcloud projects add-iam-policy-binding "$PROJECT_ID" \
     --member="serviceAccount:${SA_EMAIL}" \
     --role="roles/storage.admin"
   
   gcloud projects add-iam-policy-binding "$PROJECT_ID" \
     --member="serviceAccount:${SA_EMAIL}" \
     --role="roles/iam.serviceAccountUser"
   ```

### 错误 2: `Permission denied` 或 `Access denied`

**原因**：
- 当前用户没有足够的权限
- 服务账号权限不足

**解决方案**：

1. **检查当前用户权限**：
   ```bash
   gcloud projects get-iam-policy PROJECT_ID
   ```

2. **确保当前用户是项目所有者或有 IAM Admin 权限**

3. **使用项目所有者账号执行命令**

### 错误 3: `Service account not found`

**原因**：
- 服务账号不存在
- 服务账号邮箱拼写错误

**解决方案**：

1. **列出所有服务账号**：
   ```bash
   gcloud iam service-accounts list --project=PROJECT_ID
   ```

2. **创建服务账号**：
   ```bash
   gcloud iam service-accounts create github-actions-deployer \
     --display-name="GitHub Actions Deployer" \
     --project=PROJECT_ID
   ```

### 错误 4: `API not enabled`

**原因**：
- 必要的 GCP API 未启用

**解决方案**：

```bash
gcloud services enable \
  cloudfunctions.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  storage-api.googleapis.com \
  artifactregistry.googleapis.com \
  --project=PROJECT_ID
```

### 错误 5: `Invalid JSON in GCP_SA_KEY`

**原因**：
- GitHub Secret 中的 JSON 格式不正确
- 复制时缺少引号或转义字符

**解决方案**：

1. **验证 JSON 格式**：
   ```bash
   # 如果密钥文件在本地
   cat gcp-sa-key.json | jq .
   ```

2. **在 GitHub Secrets 中正确配置**：
   - 复制完整的 JSON 内容（包括所有大括号和引号）
   - 不要添加额外的引号或转义字符
   - 确保 JSON 是有效的

3. **使用脚本自动获取正确格式**：
   ```bash
   # 使用 jq 格式化（如果已安装）
   cat gcp-sa-key.json | jq -c .
   
   # 或直接复制文件内容
   cat gcp-sa-key.json
   ```

## 验证步骤

### 1. 验证服务账号存在

```bash
gcloud iam service-accounts describe \
  github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com
```

### 2. 验证权限

```bash
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com"
```

### 3. 验证 API 已启用

```bash
gcloud services list --enabled --project=PROJECT_ID | grep -E "cloudfunctions|cloudbuild|run"
```

### 4. 测试服务账号密钥

```bash
# 设置环境变量
export GOOGLE_APPLICATION_CREDENTIALS="gcp-sa-key.json"

# 测试认证
gcloud auth activate-service-account \
  github-actions-deployer@PROJECT_ID.iam.gserviceaccount.com \
  --key-file=gcp-sa-key.json

# 测试权限
gcloud functions list --project=PROJECT_ID
```

## 快速诊断命令

运行以下命令进行完整诊断：

```bash
#!/bin/bash
PROJECT_ID="your-project-id"
SA_EMAIL="github-actions-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

echo "1. 检查项目 ID..."
gcloud config get-value project

echo ""
echo "2. 检查服务账号..."
gcloud iam service-accounts describe "$SA_EMAIL" 2>/dev/null && echo "✅ 服务账号存在" || echo "❌ 服务账号不存在"

echo ""
echo "3. 检查权限..."
gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${SA_EMAIL}" \
  --format="table(bindings.role)"

echo ""
echo "4. 检查 API 状态..."
gcloud services list --enabled --project="$PROJECT_ID" | grep -E "cloudfunctions|cloudbuild|run" || echo "⚠️  部分 API 未启用"
```

## 获取帮助

如果以上方法都无法解决问题：

1. **查看详细错误信息**：
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:SA_EMAIL" \
     --role="roles/cloudfunctions.admin" \
     --verbosity=debug
   ```

2. **检查 gcloud 版本**：
   ```bash
   gcloud version
   # 确保使用最新版本
   gcloud components update
   ```

3. **查看 GCP 文档**：
   - [IAM 权限管理](https://cloud.google.com/iam/docs)
   - [服务账号最佳实践](https://cloud.google.com/iam/docs/service-accounts)

4. **使用 Google Cloud Console**：
   - 如果命令行工具遇到问题，可以在 Web 控制台中手动配置

## 推荐工作流程

1. ✅ 使用自动化脚本 `setup_gcp_service_account.sh`
2. ✅ 验证服务账号和权限
3. ✅ 测试密钥文件
4. ✅ 配置 GitHub Secrets
5. ✅ 测试部署
