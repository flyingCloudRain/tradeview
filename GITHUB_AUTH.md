# GitHub 认证配置指南

## 问题

推送代码到 GitHub 时出现认证失败：
```
remote: No anonymous write access.
fatal: Authentication failed
```

## 原因

GitHub 已不再支持使用密码推送，需要使用 **Personal Access Token (PAT)** 或 **SSH 密钥**。

## 解决方案

### 方案 1: 使用 Personal Access Token (PAT) - 最简单 ⭐

#### 步骤 1: 创建 Personal Access Token

1. 访问 GitHub Token 设置：
   ```
   https://github.com/settings/tokens
   ```

2. 点击 **"Generate new token"** → **"Generate new token (classic)"**

3. 设置 Token 信息：
   - **Note**: `trading_review_new` (描述用途)
   - **Expiration**: 选择过期时间（建议 90 天或 No expiration）
   - **Select scopes**: 至少勾选 `repo` (完整仓库访问权限)

4. 点击 **"Generate token"**

5. **重要**: 立即复制生成的 token（只显示一次！）
   ```
   ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

#### 步骤 2: 使用 Token 推送

```bash
# 推送代码
git push -u origin main

# 当提示输入用户名和密码时：
# Username: flyingCloudRain
# Password: <粘贴你的 token> (不是 GitHub 密码！)
```

#### 步骤 3: 保存凭证（可选，避免每次输入）

**macOS**:
```bash
# 使用 Git Credential Helper
git config --global credential.helper osxkeychain

# 推送一次后，凭证会保存在钥匙串中
git push -u origin main
```

**Linux**:
```bash
git config --global credential.helper store
```

### 方案 2: 使用 SSH 密钥

#### 步骤 1: 生成 SSH 密钥

```bash
# 生成新的 SSH 密钥（使用你的 GitHub 邮箱）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 按回车使用默认路径
# 设置密码（可选，建议设置）
```

#### 步骤 2: 添加 SSH 密钥到 GitHub

1. 复制公钥：
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # 或
   cat ~/.ssh/id_rsa.pub
   ```

2. 访问 GitHub SSH 设置：
   ```
   https://github.com/settings/keys
   ```

3. 点击 **"New SSH key"**
   - **Title**: `MacBook Air` (或你的设备名称)
   - **Key**: 粘贴刚才复制的公钥
   - 点击 **"Add SSH key"**

#### 步骤 3: 更改远程 URL 为 SSH

```bash
# 更改远程 URL
git remote set-url origin git@github.com:flyingCloudRain/tradeview.git

# 验证
git remote -v

# 推送
git push -u origin main
```

### 方案 3: 使用 GitHub CLI

```bash
# 安装 GitHub CLI (macOS)
brew install gh

# 登录
gh auth login

# 选择 GitHub.com
# 选择 HTTPS
# 选择浏览器登录或 token

# 推送
git push -u origin main
```

## 推荐方案

- **快速解决**: 使用 Personal Access Token (方案 1)
- **长期使用**: 使用 SSH 密钥 (方案 2)
- **开发工具**: 使用 GitHub CLI (方案 3)

## 当前远程仓库配置

```
origin  https://github.com/flyingCloudRain/tradeview.git
```

## 验证认证

```bash
# 测试 HTTPS 连接（需要 token）
git ls-remote origin

# 测试 SSH 连接（如果使用 SSH）
ssh -T git@github.com
```

## 常见问题

### Q1: Token 在哪里查看？

A: Token 创建后只显示一次，如果丢失需要重新创建。

### Q2: Token 过期了怎么办？

A: 创建新的 token 并更新保存的凭证。

### Q3: 如何撤销 token？

A: 访问 https://github.com/settings/tokens，找到对应 token 点击撤销。

### Q4: SSH 连接失败？

A: 检查：
- SSH 密钥是否正确添加到 GitHub
- SSH agent 是否运行：`eval "$(ssh-agent -s)"`
- 添加密钥到 agent：`ssh-add ~/.ssh/id_ed25519`

## 安全建议

1. ✅ 使用强密码保护 SSH 密钥
2. ✅ Token 设置合理的过期时间
3. ✅ 定期轮换 Token
4. ✅ 不要将 Token 提交到代码仓库
5. ✅ 使用最小权限原则（只授予必要的权限）
