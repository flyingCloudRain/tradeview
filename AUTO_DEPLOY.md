# 自动部署配置指南

## 概述

本文档介绍如何配置自动部署到 CloudBase，支持 GitHub Actions、GitLab CI/CD 等 CI/CD 平台。

## 方案一：GitHub Actions（推荐）

### 1. 配置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

1. 进入仓库：**Settings** → **Secrets and variables** → **Actions**
2. 添加以下 Secrets：

| Secret 名称 | 说明 | 获取方式 |
|------------|------|---------|
| `CLOUDBASE_ENV_ID` | CloudBase 环境 ID | `trade-view-0gtiozig72c07cd0` |
| `TCB_SECRET_ID` | 腾讯云 SecretId | [腾讯云控制台](https://console.cloud.tencent.com/cam/capi) |
| `TCB_SECRET_KEY` | 腾讯云 SecretKey | [腾讯云控制台](https://console.cloud.tencent.com/cam/capi) |

### 2. 获取腾讯云密钥

1. 访问 [腾讯云访问管理控制台](https://console.cloud.tencent.com/cam/capi)
2. 创建 API 密钥或使用现有密钥
3. 复制 **SecretId** 和 **SecretKey**

### 3. 使用工作流

已创建 `.github/workflows/deploy.yml`，会在以下情况自动触发：

- 推送到 `main` 或 `master` 分支
- 手动触发（在 Actions 页面）

### 4. 查看部署状态

在 GitHub 仓库的 **Actions** 标签页查看部署状态和日志。

## 方案二：GitLab CI/CD

### 1. 创建 `.gitlab-ci.yml`

```yaml
stages:
  - deploy

deploy:
  stage: deploy
  image: node:18
  before_script:
    - npm install -g @cloudbase/cli
    - apt-get update && apt-get install -y python3 python3-pip
  script:
    - cd frontend && npm ci && npm run build
    - cd ..
    - mkdir -p functions/trading-api
    - cp backend/index.py functions/trading-api/
    - cp backend/requirements.txt functions/trading-api/
    - cp -r backend/app functions/trading-api/
    - cloudbase functions:deploy trading-api -e $CLOUDBASE_ENV_ID
    - cloudbase hosting:deploy frontend/dist -e $CLOUDBASE_ENV_ID
  only:
    - main
    - master
```

### 2. 配置 GitLab CI/CD 变量

在 GitLab 项目设置中添加：

- `CLOUDBASE_ENV_ID`
- `TCB_SECRET_ID`
- `TCB_SECRET_KEY`

## 方案三：使用部署脚本

### 1. 本地自动部署脚本

已创建 `scripts/auto-deploy.sh`，可以通过环境变量配置：

```bash
export CLOUDBASE_ENV_ID="trade-view-0gtiozig72c07cd0"
export TCB_SECRET_ID="your-secret-id"
export TCB_SECRET_KEY="your-secret-key"

bash scripts/auto-deploy.sh
```

### 2. 在 CI/CD 中使用

```yaml
- name: Deploy
  run: bash scripts/auto-deploy.sh
  env:
    CLOUDBASE_ENV_ID: ${{ secrets.CLOUDBASE_ENV_ID }}
    TCB_SECRET_ID: ${{ secrets.TCB_SECRET_ID }}
    TCB_SECRET_KEY: ${{ secrets.TCB_SECRET_KEY }}
```

## CloudBase CLI 认证方式

### 方式 1: 使用密钥文件（推荐用于 CI/CD）

```bash
# 创建密钥文件
mkdir -p ~/.tcb
cat > ~/.tcb/login.json << EOF
{
  "secretId": "$TCB_SECRET_ID",
  "secretKey": "$TCB_SECRET_KEY"
}
EOF

# 使用密钥登录
cloudbase login --key
```

### 方式 2: 环境变量（如果 CLI 支持）

```bash
export TCB_SECRET_ID="your-secret-id"
export TCB_SECRET_KEY="your-secret-key"
cloudbase login
```

### 方式 3: 交互式登录（仅用于本地）

```bash
cloudbase login
# 会打开浏览器进行登录
```

## 部署流程

自动部署流程包括：

1. **代码检出**：从 Git 仓库检出代码
2. **环境准备**：安装 Node.js、Python、CloudBase CLI
3. **构建前端**：运行 `npm ci && npm run build`
4. **准备后端**：复制后端代码到 `functions/trading-api`
5. **部署云函数**：部署 `trading-api` 云函数
6. **部署静态网站**：部署前端静态文件

## 触发条件

### GitHub Actions

- **自动触发**：推送到 `main` 或 `master` 分支
- **手动触发**：在 Actions 页面点击 "Run workflow"

### GitLab CI/CD

- **自动触发**：推送到 `main` 或 `master` 分支
- **手动触发**：在 CI/CD → Pipelines 页面点击 "Run pipeline"

## 环境变量配置

### 必需的环境变量

- `CLOUDBASE_ENV_ID`: CloudBase 环境 ID

### 可选的环境变量

- `TCB_SECRET_ID`: 腾讯云 SecretId（用于自动登录）
- `TCB_SECRET_KEY`: 腾讯云 SecretKey（用于自动登录）
- `NODE_VERSION`: Node.js 版本（默认：18）
- `PYTHON_VERSION`: Python 版本（默认：3.9）

## 故障排查

### 1. 认证失败

**问题**：`Login failed` 或 `Authentication error`

**解决方案**：
- 检查 SecretId 和 SecretKey 是否正确
- 确认密钥有 CloudBase 访问权限
- 尝试手动登录验证密钥有效性

### 2. 环境 ID 错误

**问题**：`INVALID_ENV` 错误

**解决方案**：
- 检查 `CLOUDBASE_ENV_ID` 环境变量是否正确
- 确认环境 ID 在 CloudBase 控制台存在

### 3. 部署超时

**问题**：部署过程超时

**解决方案**：
- 增加 CI/CD 超时时间
- 检查网络连接
- 查看 CloudBase 控制台是否有错误

### 4. 构建失败

**问题**：前端或后端构建失败

**解决方案**：
- 检查代码是否有语法错误
- 确认依赖是否正确安装
- 查看构建日志定位问题

## 最佳实践

1. **使用分支保护**：只允许从 `main`/`master` 分支部署
2. **代码审查**：部署前进行代码审查
3. **测试先行**：在部署前运行测试
4. **回滚机制**：准备回滚方案
5. **监控告警**：配置部署成功/失败的告警

## 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [GitLab CI/CD 文档](https://docs.gitlab.com/ee/ci/)
- [CloudBase CLI 文档](https://docs.cloudbase.net/cli-v1/intro)
- [腾讯云 API 密钥管理](https://console.cloud.tencent.com/cam/capi)

## 示例：完整的 GitHub Actions 工作流

参考 `.github/workflows/deploy.yml` 文件，包含：

- ✅ 代码检出
- ✅ 环境设置（Node.js、Python）
- ✅ CloudBase CLI 安装
- ✅ 前端构建
- ✅ 后端准备
- ✅ 云函数部署
- ✅ 静态网站部署
- ✅ 部署摘要

## 下一步

1. 配置 GitHub Secrets
2. 推送代码到 `main` 分支
3. 查看 Actions 页面确认部署状态
4. 访问网站验证部署结果
