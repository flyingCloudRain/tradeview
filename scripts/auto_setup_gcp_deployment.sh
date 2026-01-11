#!/bin/bash

# 自动化 GCP 部署配置脚本
# 自动完成：创建服务账号、启用 API、生成 GitHub Secrets 配置

set -e

echo "=========================================="
echo "🚀 GCP 自动部署配置脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 获取项目 ID
GCP_PROJECT=${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}

if [ -z "$GCP_PROJECT" ]; then
    echo -e "${RED}❌ 错误: 未设置 GCP_PROJECT${NC}"
    echo ""
    echo "请设置环境变量:"
    echo "  export GCP_PROJECT=tradeview-484009"
    echo ""
    echo "或运行:"
    echo "  gcloud config set project tradeview-484009"
    exit 1
fi

echo -e "${GREEN}项目 ID: $GCP_PROJECT${NC}"
echo ""

# 检查是否已登录
echo "检查 Google Cloud 登录状态..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 &> /dev/null; then
    echo -e "${RED}请先登录 Google Cloud:${NC}"
    echo "  gcloud auth login"
    exit 1
fi
echo -e "${GREEN}✅ 已登录${NC}"
echo ""

# 步骤 1: 启用必要的 API
echo "=========================================="
echo "步骤 1: 启用必要的 GCP API"
echo "=========================================="

APIS=(
    "cloudfunctions.googleapis.com"
    "cloudbuild.googleapis.com"
    "run.googleapis.com"
    "storage-api.googleapis.com"
    "artifactregistry.googleapis.com"
)

for API in "${APIS[@]}"; do
    echo "启用 API: $API"
    if gcloud services enable "$API" --project="$GCP_PROJECT" 2>&1 | grep -q "already enabled"; then
        echo -e "  ${YELLOW}⚠️  已启用${NC}"
    else
        echo -e "  ${GREEN}✅ 已启用${NC}"
    fi
done
echo ""

# 步骤 2: 创建服务账号
echo "=========================================="
echo "步骤 2: 创建服务账号"
echo "=========================================="

SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SA_EMAIL" --project="$GCP_PROJECT" &>/dev/null; then
    echo -e "${GREEN}✅ 服务账号已存在: $SA_EMAIL${NC}"
else
    echo "创建服务账号: $SA_NAME"
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployer" \
        --description="Service account for GitHub Actions CI/CD deployment" \
        --project="$GCP_PROJECT"
    echo -e "${GREEN}✅ 服务账号创建成功${NC}"
fi
echo ""

# 步骤 3: 授予必要的角色
echo "=========================================="
echo "步骤 3: 授予角色权限"
echo "=========================================="

ROLES=(
    "roles/cloudfunctions.admin"
    "roles/run.admin"
    "roles/storage.admin"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.builder"
    "roles/artifactregistry.writer"
)

for ROLE in "${ROLES[@]}"; do
    echo "授予角色: $ROLE"
    if gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --condition=None &>/dev/null; then
        echo -e "  ${GREEN}✅ 成功${NC}"
    else
        echo -e "  ${YELLOW}⚠️  可能已存在，继续...${NC}"
    fi
done
echo ""

# 步骤 4: 创建并下载密钥
echo "=========================================="
echo "步骤 4: 创建服务账号密钥"
echo "=========================================="

KEY_FILE="gcp-sa-key.json"
if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}⚠️  密钥文件已存在: $KEY_FILE${NC}"
    read -p "是否覆盖? (y/n): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "使用现有密钥文件"
    else
        rm -f "$KEY_FILE"
        gcloud iam service-accounts keys create "$KEY_FILE" \
            --iam-account="$SA_EMAIL" \
            --project="$GCP_PROJECT"
        echo -e "${GREEN}✅ 密钥文件已创建${NC}"
    fi
else
    gcloud iam service-accounts keys create "$KEY_FILE" \
        --iam-account="$SA_EMAIL" \
        --project="$GCP_PROJECT"
    echo -e "${GREEN}✅ 密钥文件已创建: $KEY_FILE${NC}"
fi
echo ""

# 步骤 5: 读取密钥内容
KEY_CONTENT=$(cat "$KEY_FILE" | jq -c . 2>/dev/null || cat "$KEY_FILE")

# 步骤 6: 生成 GitHub Secrets 配置指南
echo "=========================================="
echo "步骤 5: 生成 GitHub Secrets 配置指南"
echo "=========================================="

GITHUB_REPO=${GITHUB_REPO:-""}
if [ -z "$GITHUB_REPO" ]; then
    # 尝试从 git remote 获取仓库信息
    if git remote get-url origin &>/dev/null; then
        REMOTE_URL=$(git remote get-url origin)
        if [[ $REMOTE_URL =~ github.com[:/]([^/]+)/([^/]+)\.git ]]; then
            GITHUB_REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
        fi
    fi
fi

CONFIG_FILE="github-secrets-config.md"
cat > "$CONFIG_FILE" << EOF
# GitHub Secrets 配置指南

## 📋 自动生成的配置

### 必需的 Secrets

#### 1. GCP_PROJECT_ID
\`\`\`
$GCP_PROJECT
\`\`\`

#### 2. GCP_SA_KEY
\`\`\`
$KEY_CONTENT
\`\`\`

### 可选的 Secrets（推荐配置）

#### 3. GCP_REGION
\`\`\`
us-central1
\`\`\`

#### 4. FUNCTION_NAME
\`\`\`
trading-api
\`\`\`

#### 5. FRONTEND_SERVICE_NAME
\`\`\`
trading-frontend
\`\`\`

#### 6. DATABASE_URL（如果使用 Supabase）
\`\`\`
postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
\`\`\`

#### 7. SUPABASE_URL（如果使用 Supabase）
\`\`\`
https://xxx.supabase.co
\`\`\`

#### 8. SUPABASE_KEY（如果使用 Supabase）
\`\`\`
your-supabase-key
\`\`\`

#### 9. SUPABASE_SERVICE_KEY（如果使用 Supabase）
\`\`\`
your-service-key
\`\`\`

#### 10. CORS_ORIGINS（前端部署后更新）
\`\`\`
["https://your-frontend-domain.com"]
\`\`\`

## 📝 配置步骤

1. 访问 GitHub 仓库设置：
   ${GITHUB_REPO:+https://github.com/$GITHUB_REPO/settings/secrets/actions}
   ${GITHUB_REPO:-https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions}

2. 点击 "New repository secret"

3. 依次添加上述 Secrets

## 🔐 使用 GitHub CLI 自动配置（可选）

如果已安装 GitHub CLI 并已认证，可以运行：

\`\`\`bash
# 设置必需的 Secrets
gh secret set GCP_PROJECT_ID --body "$GCP_PROJECT"
gh secret set GCP_SA_KEY --body '$KEY_CONTENT'

# 设置可选的 Secrets
gh secret set GCP_REGION --body "us-central1"
gh secret set FUNCTION_NAME --body "trading-api"
gh secret set FRONTEND_SERVICE_NAME --body "trading-frontend"
\`\`\`

## ⚠️  安全提示

- 密钥文件 \`$KEY_FILE\` 包含敏感信息，请妥善保管
- 配置完 GitHub Secrets 后，建议删除本地密钥文件：
  \`\`\`bash
  rm $KEY_FILE
  \`\`\`
- 不要将密钥文件提交到 Git 仓库

EOF

echo -e "${GREEN}✅ 配置指南已生成: $CONFIG_FILE${NC}"
echo ""

# 步骤 7: 尝试使用 GitHub CLI 自动配置（如果可用）
if command -v gh &> /dev/null && gh auth status &>/dev/null; then
    echo "=========================================="
    echo "步骤 6: 使用 GitHub CLI 自动配置 Secrets"
    echo "=========================================="
    echo ""
    read -p "是否使用 GitHub CLI 自动配置 Secrets? (y/n): " use_gh_cli
    if [ "$use_gh_cli" = "y" ] || [ "$use_gh_cli" = "Y" ]; then
        echo "配置 GCP_PROJECT_ID..."
        echo "$GCP_PROJECT" | gh secret set GCP_PROJECT_ID
        echo -e "${GREEN}✅ GCP_PROJECT_ID 已设置${NC}"
        
        echo "配置 GCP_SA_KEY..."
        echo "$KEY_CONTENT" | gh secret set GCP_SA_KEY
        echo -e "${GREEN}✅ GCP_SA_KEY 已设置${NC}"
        
        echo "配置 GCP_REGION..."
        echo "us-central1" | gh secret set GCP_REGION
        echo -e "${GREEN}✅ GCP_REGION 已设置${NC}"
        
        echo "配置 FUNCTION_NAME..."
        echo "trading-api" | gh secret set FUNCTION_NAME
        echo -e "${GREEN}✅ FUNCTION_NAME 已设置${NC}"
        
        echo "配置 FRONTEND_SERVICE_NAME..."
        echo "trading-frontend" | gh secret set FRONTEND_SERVICE_NAME
        echo -e "${GREEN}✅ FRONTEND_SERVICE_NAME 已设置${NC}"
        
        echo ""
        echo -e "${GREEN}🎉 GitHub Secrets 已自动配置完成！${NC}"
    else
        echo "跳过 GitHub CLI 配置"
    fi
else
    echo "=========================================="
    echo "步骤 6: GitHub CLI 配置"
    echo "=========================================="
    echo -e "${YELLOW}⚠️  GitHub CLI 未安装或未认证${NC}"
    echo ""
    echo "可选：安装并配置 GitHub CLI 以实现自动配置："
    echo "  1. 安装: brew install gh"
    echo "  2. 认证: gh auth login"
    echo "  3. 重新运行此脚本"
fi
echo ""

# 完成总结
echo "=========================================="
echo "🎉 配置完成！"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ GCP API 已启用${NC}"
echo -e "${GREEN}✅ 服务账号已创建: $SA_EMAIL${NC}"
echo -e "${GREEN}✅ 权限已授予${NC}"
echo -e "${GREEN}✅ 密钥文件已创建: $KEY_FILE${NC}"
echo -e "${GREEN}✅ 配置指南已生成: $CONFIG_FILE${NC}"
echo ""
echo "📋 下一步："
echo "  1. 查看配置指南: cat $CONFIG_FILE"
if [ ! -z "$GITHUB_REPO" ]; then
    echo "  2. 配置 GitHub Secrets: https://github.com/$GITHUB_REPO/settings/secrets/actions"
else
    echo "  2. 配置 GitHub Secrets: https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
fi
echo "  3. 推送代码测试部署: git push origin main"
echo ""
echo -e "${YELLOW}⚠️  重要：配置完 GitHub Secrets 后，建议删除本地密钥文件：${NC}"
echo "  rm $KEY_FILE"
echo ""
