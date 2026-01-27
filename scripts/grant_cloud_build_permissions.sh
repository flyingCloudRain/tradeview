#!/bin/bash

# 使用 github-actions-deployer 服务账号授予 Cloud Build 服务账号权限
# 需要先授予 github-actions-deployer 服务账号 roles/resourcemanager.projectIamAdmin 权限

set -e

echo "=========================================="
echo "授予 Cloud Build 服务账号权限"
echo "=========================================="
echo ""

# 获取项目 ID
GCP_PROJECT=${GCP_PROJECT:-"tradeview-484009"}
GITHUB_SA="github-actions-deployer@${GCP_PROJECT}.iam.gserviceaccount.com"

echo "项目 ID: $GCP_PROJECT"
echo "GitHub Actions 服务账号: $GITHUB_SA"
echo ""

# 检查是否已登录或使用服务账号
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 &> /dev/null; then
    echo "❌ 错误: 未登录 Google Cloud"
    echo ""
    echo "请选择以下方式之一："
    echo ""
    echo "方式 1: 使用项目所有者账号登录"
    echo "  gcloud auth login"
    echo ""
    echo "方式 2: 使用 github-actions-deployer 服务账号"
    echo "  gcloud auth activate-service-account $GITHUB_SA --key-file=path/to/gcp-sa-key.json"
    echo ""
    exit 1
fi

CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo "当前使用的账号: $CURRENT_ACCOUNT"
echo ""

# 设置项目
gcloud config set project $GCP_PROJECT

# 获取项目编号和 Cloud Build 服务账号
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

echo "Cloud Build 服务账号: $CLOUD_BUILD_SA"
echo ""

# 授予必要的角色
echo "=========================================="
echo "授予 Cloud Build 服务账号权限"
echo "=========================================="

ROLES=(
    "roles/serviceusage.serviceUsageConsumer"
    "roles/run.admin"
    "roles/iam.serviceAccountUser"
    "roles/storage.admin"
)

for ROLE in "${ROLES[@]}"; do
    echo "授予角色: $ROLE"
    if gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
        --member="serviceAccount:${CLOUD_BUILD_SA}" \
        --role="$ROLE" \
        --condition=None 2>&1; then
        echo "  ✅ 成功"
    else
        echo "  ⚠️  失败或权限已存在"
    fi
    echo ""
done

echo "=========================================="
echo "权限授予完成"
echo "=========================================="
echo ""

# 验证权限
echo "验证权限..."
gcloud projects get-iam-policy "$GCP_PROJECT" \
  --flatten="bindings[].members" \
  --filter="bindings.members:${CLOUD_BUILD_SA}" \
  --format="table(bindings.role)" || echo "⚠️ 无法验证权限"

echo ""
echo "✅ 完成！现在可以重新运行 GitHub Actions 工作流了。"
