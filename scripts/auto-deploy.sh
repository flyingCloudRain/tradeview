#!/bin/bash

# 自动部署脚本（用于 CI/CD）
# 支持通过环境变量配置认证信息

set -e

echo "=========================================="
echo "自动部署到 CloudBase"
echo "=========================================="

# 检查必需的环境变量
if [ -z "$CLOUDBASE_ENV_ID" ]; then
    echo "错误: 未设置 CLOUDBASE_ENV_ID 环境变量"
    exit 1
fi

# 检查 CloudBase CLI
if ! command -v cloudbase &> /dev/null && ! command -v tcb &> /dev/null; then
    echo "安装 CloudBase CLI..."
    npm install -g @cloudbase/cli
fi

# 登录 CloudBase（如果提供了密钥）
if [ -n "$TCB_SECRET_ID" ] && [ -n "$TCB_SECRET_KEY" ]; then
    echo "使用密钥登录 CloudBase..."
    # 注意：CloudBase CLI 可能需要不同的登录方式
    # 这里需要根据实际情况调整
    echo "请配置 CloudBase CLI 的认证方式"
fi

# 构建前端
echo "构建前端..."
cd frontend
npm ci
npm run build
cd ..

# 准备后端
echo "准备后端代码..."
mkdir -p functions/trading-api
cp backend/index.py functions/trading-api/
cp backend/requirements.txt functions/trading-api/
cp -r backend/app functions/trading-api/

if ! grep -q "mangum" functions/trading-api/requirements.txt; then
    echo "mangum>=0.17.0" >> functions/trading-api/requirements.txt
fi

# 部署云函数
echo "部署云函数..."
cloudbase functions:deploy trading-api -e "$CLOUDBASE_ENV_ID" --force

# 部署静态网站
echo "部署静态网站..."
cloudbase hosting:deploy frontend/dist -e "$CLOUDBASE_ENV_ID"

echo "=========================================="
echo "部署完成！"
echo "=========================================="
