#!/bin/bash

# 重启本地开发环境脚本
# 先停止现有服务，然后重新启动

set +e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "重启本地开发环境"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 停止现有服务
echo -e "${BLUE}步骤 1: 停止现有服务...${NC}"
echo ""

# 查找并停止后端进程（uvicorn）
BACKEND_PIDS=$(ps aux | grep "uvicorn app.main:app" | grep -v grep | awk '{print $2}')
if [ -n "$BACKEND_PIDS" ]; then
    echo "找到后端进程: $BACKEND_PIDS"
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 后端服务已停止${NC}"
else
    echo -e "${YELLOW}未找到运行中的后端服务${NC}"
fi

# 查找并停止前端进程（vite）
FRONTEND_PIDS=$(ps aux | grep "vite\|npm run dev" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    echo "找到前端进程: $FRONTEND_PIDS"
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null || true
    echo -e "${GREEN}✅ 前端服务已停止${NC}"
else
    echo -e "${YELLOW}未找到运行中的前端服务${NC}"
fi

# 等待进程完全停止
echo ""
echo "等待进程完全停止..."
sleep 2

# 检查端口占用
echo ""
echo -e "${BLUE}步骤 2: 检查端口占用...${NC}"

# 检查后端端口 8000
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PORT_PID=$(lsof -Pi :8000 -sTCP:LISTEN -t)
    echo -e "${YELLOW}⚠️  端口 8000 仍被占用 (PID: $PORT_PID)，正在强制释放...${NC}"
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 1
fi

# 检查前端端口 3000
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PORT_PID=$(lsof -Pi :3000 -sTCP:LISTEN -t)
    echo -e "${YELLOW}⚠️  端口 3000 仍被占用 (PID: $PORT_PID)，正在强制释放...${NC}"
    kill -9 $PORT_PID 2>/dev/null || true
    sleep 1
fi

echo -e "${GREEN}✅ 端口检查完成${NC}"
echo ""

# 重新启动服务
echo -e "${BLUE}步骤 3: 重新启动服务...${NC}"
echo ""

# 调用启动脚本
if [ -f "$SCRIPT_DIR/start_dev.sh" ]; then
    echo "执行启动脚本: $SCRIPT_DIR/start_dev.sh"
    echo ""
    exec "$SCRIPT_DIR/start_dev.sh"
else
    echo -e "${RED}❌ 错误: 未找到启动脚本 start_dev.sh${NC}"
    echo "请确保脚本存在于: $SCRIPT_DIR/start_dev.sh"
    exit 1
fi
