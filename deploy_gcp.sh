#!/bin/bash

# Google Cloud Functions 部署脚本

set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "开始部署到 Google Cloud Functions..."
echo "=========================================="
echo "当前工作目录: $(pwd)"
echo ""

# 检查是否已安装 Google Cloud SDK
if ! command -v gcloud &> /dev/null; then
    echo "❌ 错误: 未安装 Google Cloud SDK"
    echo "请访问: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 检查是否已登录
echo "检查 Google Cloud 登录状态..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 &> /dev/null; then
    echo "请先登录 Google Cloud:"
    echo "gcloud auth login"
    exit 1
fi
echo "✅ 已登录"
echo ""

# 读取配置
GCP_PROJECT=${GCP_PROJECT:-$(gcloud config get-value project 2>/dev/null)}
GCP_REGION=${GCP_REGION:-"us-central1"}
FUNCTION_NAME=${FUNCTION_NAME:-"trading-api"}
RUNTIME=${RUNTIME:-"python311"}
MEMORY=${MEMORY:-"512MB"}
TIMEOUT=${TIMEOUT:-"540s"}
MAX_INSTANCES=${MAX_INSTANCES:-"10"}

if [ -z "$GCP_PROJECT" ]; then
    echo "❌ 错误: 未设置 GCP_PROJECT"
    echo "请设置环境变量: export GCP_PROJECT=your-project-id"
    echo "或运行: gcloud config set project your-project-id"
    exit 1
fi

echo "配置信息:"
echo "  项目 ID: $GCP_PROJECT"
echo "  区域: $GCP_REGION"
echo "  函数名称: $FUNCTION_NAME"
echo "  运行时: $RUNTIME"
echo "  内存: $MEMORY"
echo "  超时: $TIMEOUT"
echo ""

# 1. 构建前端
echo ""
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

cd ..

# 2. 运行数据库迁移（可选）
echo ""
echo "=========================================="
echo "步骤 2: 数据库迁移（可选）..."
echo "=========================================="

if [ -n "$DATABASE_URL" ]; then
    echo "检测到 DATABASE_URL，尝试运行数据库迁移..."
    cd backend
    
    # 加载 .env 文件（如果存在）
    if [ -f ".env" ]; then
        echo "加载 .env 文件..."
        set -a
        source .env
        set +a
    fi
    
    # 检查是否安装了 alembic
    if command -v alembic &> /dev/null || python3 -m alembic --help &> /dev/null; then
        echo "运行数据库迁移..."
        if command -v alembic &> /dev/null; then
            alembic upgrade head
        else
            python3 -m alembic upgrade head
        fi
        echo "✅ 数据库迁移完成"
    else
        echo "⚠️  Alembic 未安装，跳过本地迁移"
    fi
    
    cd ..
else
    echo "⚠️  DATABASE_URL 未设置，跳过数据库迁移"
fi

# 3. 部署后端 Cloud Function
echo ""
echo "=========================================="
echo "步骤 3: 部署 Google Cloud Function..."
echo "=========================================="

cd backend

# 准备环境变量
ENV_VARS=""
if [ -n "$DATABASE_URL" ]; then
    ENV_VARS="$ENV_VARS,DATABASE_URL=$DATABASE_URL"
fi
if [ -n "$SUPABASE_URL" ]; then
    ENV_VARS="$ENV_VARS,SUPABASE_URL=$SUPABASE_URL"
fi
if [ -n "$SUPABASE_KEY" ]; then
    ENV_VARS="$ENV_VARS,SUPABASE_KEY=$SUPABASE_KEY"
fi
if [ -n "$SUPABASE_SERVICE_KEY" ]; then
    ENV_VARS="$ENV_VARS,SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY"
fi
if [ -n "$CORS_ORIGINS" ]; then
    ENV_VARS="$ENV_VARS,CORS_ORIGINS=$CORS_ORIGINS"
fi

# 移除开头的逗号
ENV_VARS=${ENV_VARS#,}

echo "部署 Cloud Function..."
echo "  入口点: cloud_function"
echo "  源目录: ."
echo "  环境变量: ${ENV_VARS:0:100}..."

# 构建部署命令
DEPLOY_CMD="gcloud functions deploy $FUNCTION_NAME \
    --gen2 \
    --runtime=$RUNTIME \
    --region=$GCP_REGION \
    --source=. \
    --entry-point=main \
    --trigger-http \
    --allow-unauthenticated \
    --memory=$MEMORY \
    --timeout=$TIMEOUT \
    --max-instances=$MAX_INSTANCES \
    --set-env-vars=$ENV_VARS"

echo "执行命令: $DEPLOY_CMD"
eval $DEPLOY_CMD

cd ..

# 4. 部署前端到 Cloud Storage（可选）
echo ""
echo "=========================================="
echo "步骤 4: 部署前端（可选）..."
echo "=========================================="

read -p "是否部署前端到 Cloud Storage? (y/n): " deploy_frontend

if [ "$deploy_frontend" = "y" ] || [ "$deploy_frontend" = "Y" ]; then
    BUCKET_NAME=${BUCKET_NAME:-"${GCP_PROJECT}-frontend"}
    
    echo "创建 Cloud Storage 存储桶（如果不存在）..."
    gsutil mb -p "$GCP_PROJECT" -l "$GCP_REGION" "gs://$BUCKET_NAME" 2>/dev/null || echo "存储桶已存在"
    
    echo "设置存储桶为网站托管..."
    gsutil web set -m index.html -e index.html "gs://$BUCKET_NAME"
    
    echo "上传前端文件..."
    gsutil -m rsync -r -d frontend/dist "gs://$BUCKET_NAME"
    
    echo "✅ 前端已部署到: https://storage.googleapis.com/$BUCKET_NAME/index.html"
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "Cloud Function URL:"
gcloud functions describe $FUNCTION_NAME --gen2 --region=$GCP_REGION --format="value(serviceConfig.uri)" 2>/dev/null || echo "运行以下命令获取 URL:"
echo "  gcloud functions describe $FUNCTION_NAME --gen2 --region=$GCP_REGION --format='value(serviceConfig.uri)'"
echo ""
echo "项目 ID: $GCP_PROJECT"
echo "区域: $GCP_REGION"
echo ""
