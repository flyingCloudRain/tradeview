#!/bin/bash

# 为 github-actions-deployer 服务账号添加缺失的权限
# 当前已有权限：
# - Artifact Registry Writer
# - Cloud Build Service Account
# - Cloud Functions Admin
# - Cloud Run Admin
# - Service Account User
# - Storage Admin
#
# 需要添加的权限：
# - Service Usage Consumer (用于使用 GCP 服务)
# - Resource Manager Project IAM Admin (可选，用于授予其他服务账号权限)

set -e

echo "=========================================="
echo "为 github-actions-deployer 添加缺失权限"
echo "=========================================="
echo ""

# 获取项目 ID
GCP_PROJECT=${GCP_PROJECT:-"tradeview-484009"}
GITHUB_SA="github-actions-deployer@${GCP_PROJECT}.iam.gserviceaccount.com"

echo "项目 ID: $GCP_PROJECT"
echo "服务账号: $GITHUB_SA"
echo ""

# 检查是否已登录
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 &> /dev/null; then
    echo "❌ 错误: 未登录 Google Cloud"
    echo "请先登录: gcloud auth login"
    exit 1
fi

CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo "当前使用的账号: $CURRENT_ACCOUNT"
echo ""

# 设置项目
gcloud config set project $GCP_PROJECT

# 需要添加的权限
MISSING_ROLES=(
    "roles/serviceusage.serviceUsageConsumer"
)

# 可选权限（如果需要授予其他服务账号权限）
OPTIONAL_ROLES=(
    "roles/resourcemanager.projectIamAdmin"
)

echo "=========================================="
echo "添加必需权限"
echo "=========================================="

for ROLE in "${MISSING_ROLES[@]}"; do
    echo "添加角色: $ROLE"
    if gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
        --member="serviceAccount:${GITHUB_SA}" \
        --role="$ROLE" \
        --condition=None 2>&1; then
        echo "  ✅ 成功"
    else
        echo "  ⚠️  失败或权限已存在"
    fi
    echo ""
done

echo "=========================================="
echo "可选权限（用于授予其他服务账号权限）"
echo "=========================================="
echo ""
read -p "是否添加 Resource Manager Project IAM Admin 权限？(y/n): " add_iam_admin

if [ "$add_iam_admin" = "y" ] || [ "$add_iam_admin" = "Y" ]; then
    for ROLE in "${OPTIONAL_ROLES[@]}"; do
        echo "添加角色: $ROLE"
        if gcloud projects add-iam-policy-binding "$GCP_PROJECT" \
            --member="serviceAccount:${GITHUB_SA}" \
            --role="$ROLE" \
            --condition=None 2>&1; then
            echo "  ✅ 成功"
        else
            echo "  ⚠️  失败或权限已存在"
        fi
        echo ""
    done
else
    echo "跳过可选权限"
fi

echo "=========================================="
echo "权限添加完成"
echo "=========================================="
echo ""

# 验证权限
echo "验证当前权限..."
gcloud projects get-iam-policy "$GCP_PROJECT" \
  --flatten="bindings[].members" \
  --filter="bindings.members:${GITHUB_SA}" \
  --format="table(bindings.role)" || echo "⚠️ 无法验证权限"

echo ""
echo "✅ 完成！"
