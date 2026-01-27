#!/bin/bash

# GCP 服务账号设置脚本
# 用于配置 GitHub Actions 自动部署所需的服务账号和权限

set -e

echo "=========================================="
echo "GCP 服务账号设置脚本"
echo "=========================================="
echo ""

# 获取项目 ID
GCP_PROJECT=${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}

if [ -z "$GCP_PROJECT" ]; then
    echo "❌ 错误: 未设置 GCP_PROJECT"
    echo ""
    echo "请设置环境变量:"
    echo "  export GCP_PROJECT=your-project-id"
    echo ""
    echo "或运行:"
    echo "  gcloud config set project your-project-id"
    exit 1
fi

echo "项目 ID: $GCP_PROJECT"
echo ""

# 服务账号名称
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

# 检查是否已登录
echo "检查 Google Cloud 登录状态..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 &> /dev/null; then
    echo "请先登录 Google Cloud:"
    echo "  gcloud auth login"
    exit 1
fi
echo "✅ 已登录"
echo ""

# 步骤 1: 创建服务账号（如果不存在）
echo "=========================================="
echo "步骤 1: 创建服务账号"
echo "=========================================="

if gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null; then
    echo "✅ 服务账号已存在: $SA_EMAIL"
else
    echo "创建服务账号: $SA_NAME"
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployer" \
        --description="Service account for GitHub Actions CI/CD deployment" \
        --project="$GCP_PROJECT"
    echo "✅ 服务账号创建成功"
fi
echo ""

# 步骤 2: 授予必要的角色
echo "=========================================="
echo "步骤 2: 授予角色权限"
echo "=========================================="

ROLES=(
    "roles/cloudfunctions.admin"
    "roles/run.admin"
    "roles/storage.admin"
    "roles/iam.serviceAccountUser"
    "roles/cloudbuild.builds.builder"
    "roles/artifactregistry.writer"
    "roles/serviceusage.serviceUsageConsumer"
)

for ROLE in "${ROLES[@]}"; do
    echo "授予角色: $ROLE"
    if gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
        --member="serviceAccount:${SA_EMAIL}" \
        --role="$ROLE" \
        --condition=None &>/dev/null; then
        echo "  ✅ 成功"
    else
        echo "  ⚠️  可能已存在或失败，继续..."
    fi
done
echo ""

# 步骤 2.5: 授予 Cloud Build 服务账号权限
echo "=========================================="
echo "步骤 2.5: 授予 Cloud Build 服务账号权限"
echo "=========================================="

PROJECT_NUMBER=$(gcloud projects describe "$GCP_PROJECT" --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "Cloud Build 服务账号: $CLOUD_BUILD_SA"

CLOUD_BUILD_ROLES=(
    "roles/serviceusage.serviceUsageConsumer"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
)

for ROLE in "${CLOUD_BUILD_ROLES[@]}"; do
    echo "授予 Cloud Build 服务账号角色: $ROLE"
    if gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
        --member="serviceAccount:${CLOUD_BUILD_SA}" \
        --role="$ROLE" \
        --condition=None &>/dev/null; then
        echo "  ✅ 成功"
    else
        echo "  ⚠️  可能已存在或失败，继续..."
    fi
done
echo ""

# 步骤 3: 创建并下载密钥
echo "=========================================="
echo "步骤 3: 创建服务账号密钥"
echo "=========================================="

KEY_FILE="gcp-sa-key.json"
echo "创建密钥文件: $KEY_FILE"

if [ -f "$KEY_FILE" ]; then
    read -p "密钥文件已存在，是否覆盖? (y/n): " overwrite
    if [ "$overwrite" != "y" ] && [ "$overwrite" != "Y" ]; then
        echo "跳过密钥创建"
        exit 0
    fi
fi

gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$GCP_PROJECT"

echo ""
echo "✅ 密钥文件已创建: $KEY_FILE"
echo ""

# 步骤 4: 显示配置信息
echo "=========================================="
echo "配置完成！"
echo "=========================================="
echo ""
echo "📋 下一步：配置 GitHub Secrets"
echo ""
echo "1. 访问 GitHub 仓库设置："
echo "   https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo ""
echo "2. 添加以下 Secrets："
echo ""
echo "   Secret 名称: GCP_PROJECT_ID"
echo "   Secret 值: $GCP_PROJECT"
echo ""
echo "   Secret 名称: GCP_SA_KEY"
echo "   Secret 值: $(cat $KEY_FILE | jq -c . 2>/dev/null || cat $KEY_FILE)"
echo ""
echo "⚠️  重要：密钥文件包含敏感信息，请妥善保管！"
echo "   建议在配置完 GitHub Secrets 后删除本地密钥文件："
echo "   rm $KEY_FILE"
echo ""
