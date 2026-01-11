# 自动化 GCP 部署配置

## 🚀 一键自动配置

### 快速开始

```bash
# 1. 设置项目 ID
export GCP_PROJECT=tradeview-484009
gcloud config set project tradeview-484009

# 2. 运行全自动配置脚本
./scripts/auto_setup_gcp_deployment.sh
```

### 脚本功能

全自动配置脚本会自动完成以下所有步骤：

1. ✅ **启用必要的 GCP API**
   - Cloud Functions API
   - Cloud Build API
   - Cloud Run API
   - Storage API
   - Artifact Registry API

2. ✅ **创建服务账号**
   - 名称：`github-actions-deployer`
   - 自动检测是否已存在

3. ✅ **授予必要权限**
   - Cloud Functions Admin
   - Cloud Run Admin
   - Storage Admin
   - Service Account User
   - Cloud Build Builder
   - Artifact Registry Writer

4. ✅ **创建服务账号密钥**
   - 生成 `gcp-sa-key.json` 文件
   - 自动处理已存在的情况

5. ✅ **生成配置指南**
   - 创建 `github-secrets-config.md` 文件
   - 包含所有 Secrets 的配置说明

6. ✅ **可选：自动配置 GitHub Secrets**
   - 如果安装了 GitHub CLI 并已认证
   - 可以自动将 Secrets 配置到 GitHub

### 使用 GitHub CLI 自动配置 Secrets

如果已安装 GitHub CLI：

```bash
# 安装 GitHub CLI（如果未安装）
brew install gh

# 登录 GitHub
gh auth login

# 运行自动配置脚本
./scripts/auto_setup_gcp_deployment.sh

# 脚本会询问是否使用 GitHub CLI 自动配置
# 输入 'y' 即可自动配置所有 Secrets
```

### 手动配置 Secrets

如果不想使用 GitHub CLI，脚本会生成配置指南：

```bash
# 查看配置指南
cat github-secrets-config.md

# 然后手动在 GitHub 仓库设置中添加 Secrets
# https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
```

### 配置完成后

1. ✅ 验证配置：
   ```bash
   # 检查服务账号
   gcloud iam service-accounts describe github-actions-deployer@tradeview-484009.iam.gserviceaccount.com
   
   # 检查 API 状态
   gcloud services list --enabled --project=tradeview-484009
   ```

2. ✅ 测试部署：
   ```bash
   git add .
   git commit -m "Setup auto deployment"
   git push origin main
   ```

3. ✅ 查看部署状态：
   - 访问 GitHub 仓库的 Actions 标签页
   - 查看 workflow 运行状态

### 安全提示

⚠️ **重要**：
- 密钥文件 `gcp-sa-key.json` 包含敏感信息
- 配置完 GitHub Secrets 后，建议删除本地密钥文件：
  ```bash
  rm gcp-sa-key.json
  ```
- 不要将密钥文件提交到 Git 仓库
- 确保 `.gitignore` 中包含 `*.json` 或 `gcp-sa-key.json`

### 故障排查

#### 问题 1: 权限不足
```bash
# 确保使用有足够权限的账号登录
gcloud auth list

# 如果需要，使用管理员账号登录
gcloud auth login
```

#### 问题 2: API 启用失败
```bash
# 手动启用 API
gcloud services enable cloudfunctions.googleapis.com --project=tradeview-484009
```

#### 问题 3: GitHub CLI 未安装
```bash
# macOS
brew install gh

# 其他系统：https://cli.github.com/
```

### 相关脚本

- `scripts/auto_setup_gcp_deployment.sh` - 全自动配置脚本（推荐）
- `scripts/setup_gcp_service_account.sh` - 基础服务账号配置脚本

### 相关文档

- [快速开始指南](../GITHUB_ACTIONS_QUICK_START.md)
- [完整配置指南](../AUTO_DEPLOY_GCP.md)
- [GitHub Actions 设置](../GITHUB_ACTIONS_SETUP.md)
