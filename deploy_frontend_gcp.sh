#!/bin/bash

# 前端部署到 Cloud Run 脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "部署前端到 Google Cloud Run..."
echo "=========================================="
echo ""

# 检查是否已安装 Google Cloud SDK
if ! command -v gcloud &> /dev/null; then
    echo "❌ 错误: 未安装 Google Cloud SDK"
    exit 1
fi

# 读取配置
GCP_PROJECT=${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}
GCP_REGION=${GCP_REGION:-"us-central1"}
SERVICE_NAME=${SERVICE_NAME:-"trading-frontend"}

if [ -z "$GCP_PROJECT" ]; then
    echo "❌ 错误: 未设置 GCP_PROJECT"
    exit 1
fi

echo "配置信息:"
echo "  项目 ID: $GCP_PROJECT"
echo "  区域: $GCP_REGION"
echo "  服务名称: $SERVICE_NAME"
echo ""

# 1. 构建前端
echo "=========================================="
echo "步骤 1: 构建前端项目..."
echo "=========================================="
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "构建前端..."
npm run build

if [ ! -d "dist" ]; then
    echo "❌ 错误: 构建失败，dist 目录不存在"
    exit 1
fi

echo "✅ 前端构建完成"
echo ""

# 2. 部署到 Cloud Run
echo "=========================================="
echo "步骤 2: 部署到 Cloud Run..."
echo "=========================================="

gcloud run deploy $SERVICE_NAME \
    --source=. \
    --platform=managed \
    --region=$GCP_REGION \
    --allow-unauthenticated \
    --port=80 \
    --memory=512Mi \
    --timeout=300

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "前端访问地址:"
gcloud run services describe $SERVICE_NAME --region=$GCP_REGION --format="value(status.url)" 2>/dev/null || echo "运行以下命令获取 URL:"
echo "  gcloud run services describe $SERVICE_NAME --region=$GCP_REGION --format='value(status.url)'"
echo ""
