#!/bin/bash

# CloudBase 部署脚本

set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "开始部署到 CloudBase..."
echo "=========================================="
echo "当前工作目录: $(pwd)"
echo ""

# 检查是否已安装 CloudBase CLI
if ! command -v cloudbase &> /dev/null && ! command -v tcb &> /dev/null; then
    echo "错误: 未安装 CloudBase CLI"
    echo "请运行: npm install -g @cloudbase/cli"
    exit 1
fi

# 检查配置文件
if [ ! -f "cloudbaserc.json" ]; then
    echo "错误: 未找到 cloudbaserc.json 配置文件"
    exit 1
fi

# 读取环境 ID
ENV_ID=$(grep -o '"envId":\s*"[^"]*"' cloudbaserc.json | cut -d'"' -f4)
if [ -z "$ENV_ID" ]; then
    echo "错误: 无法从 cloudbaserc.json 读取环境 ID"
    exit 1
fi

echo "环境 ID: $ENV_ID"
echo ""

# 检查是否已登录（使用新命令格式）
echo "检查 CloudBase 登录状态..."
if command -v tcb &> /dev/null; then
    if ! tcb env list &> /dev/null; then
        echo "请先登录 CloudBase:"
        echo "tcb login"
        exit 1
    fi
else
    if ! cloudbase env:list &> /dev/null; then
        echo "请先登录 CloudBase:"
        echo "cloudbase login"
        exit 1
    fi
fi
echo "✅ 已登录"
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
    echo "错误: 构建失败，dist 目录不存在"
    exit 1
fi

cd ..

# 2. 部署后端云函数
echo ""
echo "=========================================="
echo "步骤 2: 部署后端云函数..."
echo "=========================================="

# 确保 functions/trading-api 目录存在并包含最新代码
if [ ! -d "functions/trading-api" ]; then
    echo "创建 functions/trading-api 目录..."
    mkdir -p functions/trading-api
fi

echo "同步后端代码到 functions/trading-api..."
cp backend/index.py functions/trading-api/
cp backend/requirements.txt functions/trading-api/
cp -r backend/app functions/trading-api/

# 检查是否安装了 mangum
if ! grep -q "mangum" functions/trading-api/requirements.txt; then
    echo "添加 mangum 到 requirements.txt..."
    echo "mangum>=0.17.0" >> functions/trading-api/requirements.txt
fi

echo "部署云函数 trading-api..."
# 使用明确的环境 ID 避免 INVALID_ENV 错误
if command -v tcb &> /dev/null; then
    # 使用新命令格式
    tcb fn deploy trading-api --config-file cloudbaserc.json || \
    cloudbase functions:deploy trading-api -e "$ENV_ID" || \
    cloudbase functions:deploy trading-api
else
    # 使用旧命令格式，明确指定环境 ID
    cloudbase functions:deploy trading-api -e "$ENV_ID" || \
    cloudbase functions:deploy trading-api
fi

# 3. 部署前端静态网站
echo ""
echo "=========================================="
echo "步骤 3: 部署前端静态网站..."
echo "=========================================="

# 确保 dist 目录存在
if [ ! -d "frontend/dist" ]; then
    echo "警告: frontend/dist 目录不存在，尝试重新构建..."
    cd frontend
    npm run build
    cd ..
    
    if [ ! -d "frontend/dist" ]; then
        echo "错误: 前端构建失败，dist 目录仍然不存在"
        exit 1
    fi
fi

echo "部署前端静态网站..."
# 使用明确的环境 ID 避免 INVALID_ENV 错误
if command -v tcb &> /dev/null; then
    # 使用新命令格式
    tcb hosting deploy frontend/dist --config-file cloudbaserc.json || \
    cloudbase hosting:deploy frontend/dist -e "$ENV_ID" || \
    cloudbase hosting:deploy frontend/dist
else
    # 使用旧命令格式，明确指定环境 ID
    cloudbase hosting:deploy frontend/dist -e "$ENV_ID" || \
    cloudbase hosting:deploy frontend/dist
fi

echo ""
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "请检查 CloudBase 控制台获取访问地址："
echo "1. 云函数地址: https://${ENV_ID}.ap-shanghai.app.tcloudbase.com/trading-api"
echo "2. 静态网站地址: https://${ENV_ID}.tcloudbaseapp.com"
echo ""
echo "环境 ID: $ENV_ID"
echo "记得更新前端环境变量中的 API 地址！"
echo ""
echo "如果遇到 INVALID_ENV 错误，请查看 FIX_INVALID_ENV.md 获取解决方案"