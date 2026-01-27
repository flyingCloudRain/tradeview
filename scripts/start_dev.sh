#!/bin/bash

# 本地开发环境启动脚本
# 同时启动前端和后端服务

# 不使用 set -e，以便更好地处理错误
set +e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "启动本地开发环境"
echo "=========================================="
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端依赖
echo -e "${BLUE}检查后端依赖...${NC}"
cd "$PROJECT_ROOT/backend"
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}⚠️  未检测到虚拟环境，建议创建虚拟环境：${NC}"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    read -p "是否继续？(y/n): " continue_choice
    if [ "$continue_choice" != "y" ] && [ "$continue_choice" != "Y" ]; then
        exit 0
    fi
fi

# 检查前端依赖
echo -e "${BLUE}检查前端依赖...${NC}"
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}⚠️  未检测到 node_modules，正在安装依赖...${NC}"
    npm install
fi

# 创建日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 清理函数
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止服务...${NC}"
    [ -n "$BACKEND_PID" ] && kill $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && kill $FRONTEND_PID 2>/dev/null || true
    # 等待进程结束
    [ -n "$BACKEND_PID" ] && wait $BACKEND_PID 2>/dev/null || true
    [ -n "$FRONTEND_PID" ] && wait $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✅ 服务已停止${NC}"
    exit 0
}

# 初始化PID变量
BACKEND_PID=""
FRONTEND_PID=""

# 注册清理函数
trap cleanup SIGINT SIGTERM

# 启动后端
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}启动后端服务 (FastAPI)${NC}"
echo -e "${BLUE}==========================================${NC}"
cd "$PROJECT_ROOT/backend"

# 初始化后端启动标志
SKIP_BACKEND=false

# 检查环境变量
if [ -z "$DATABASE_URL" ]; then
    echo -e "${YELLOW}⚠️  警告: DATABASE_URL 环境变量未设置${NC}"
    echo "   后端服务可能无法正常启动"
    echo "   请设置 DATABASE_URL 或使用: source backend/setup_env.sh"
    echo ""
    read -p "是否继续启动后端？(y/n): " continue_backend
    if [ "$continue_backend" != "y" ] && [ "$continue_backend" != "Y" ]; then
        echo -e "${YELLOW}跳过后端启动${NC}"
        SKIP_BACKEND=true
    else
        echo -e "${YELLOW}继续启动后端（可能会失败）${NC}"
    fi
fi

# 检查是否有虚拟环境
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 启动后端（后台运行）
if [ "$SKIP_BACKEND" = false ]; then
    uvicorn app.main:app --reload --port 8000 --host 0.0.0.0 > "$LOG_DIR/backend.log" 2>&1 &
    BACKEND_PID=$!
fi

if [ -n "$BACKEND_PID" ]; then
    echo -e "${GREEN}✅ 后端服务已启动 (PID: $BACKEND_PID)${NC}"
    echo "   日志文件: $LOG_DIR/backend.log"
    echo "   API 文档: http://localhost:8000/docs"
    echo ""
    
    # 等待后端启动
    echo "等待后端服务启动..."
    sleep 3
    
    # 检查后端是否启动成功
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${YELLOW}⚠️  后端启动失败，查看日志:${NC}"
        tail -20 "$LOG_DIR/backend.log"
        echo -e "${YELLOW}⚠️  后端服务启动失败，但将继续启动前端服务${NC}"
        BACKEND_PID=""
    else
        echo -e "${GREEN}✅ 后端服务运行正常${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  后端服务未启动${NC}"
fi
echo ""

# 启动前端
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}启动前端服务 (Vite)${NC}"
echo -e "${BLUE}==========================================${NC}"
cd "$PROJECT_ROOT/frontend"

# 启动前端（后台运行）
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo -e "${GREEN}✅ 前端服务已启动 (PID: $FRONTEND_PID)${NC}"
echo "   日志文件: $LOG_DIR/frontend.log"
echo "   前端地址: http://localhost:3000 (或查看日志中的实际端口)"
echo ""

# 等待前端启动
echo "等待前端服务启动..."
sleep 3

# 检查前端是否启动成功
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${YELLOW}⚠️  前端启动失败，查看日志:${NC}"
    tail -20 "$LOG_DIR/frontend.log"
    echo -e "${YELLOW}⚠️  前端服务启动失败${NC}"
    FRONTEND_PID=""
else
    echo -e "${GREEN}✅ 前端服务运行正常${NC}"
fi

# 显示服务状态
echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✅ 所有服务已启动${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "📋 服务信息:"
if [ -n "$BACKEND_PID" ]; then
    echo "   后端 API:  http://localhost:8000"
    echo "   API 文档:  http://localhost:8000/docs"
else
    echo "   后端 API:  (未启动)"
fi
if [ -n "$FRONTEND_PID" ]; then
    echo "   前端应用:  http://localhost:3000"
else
    echo "   前端应用:  (未启动)"
fi
echo ""
echo "📝 日志文件:"
echo "   后端日志:  $LOG_DIR/backend.log"
echo "   前端日志:  $LOG_DIR/frontend.log"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止所有服务${NC}"
echo ""

# 保持脚本运行，持续监控进程状态
while true; do
    sleep 5
    # 检查后端进程
    if [ -n "$BACKEND_PID" ] && ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${YELLOW}⚠️  后端服务已停止 (PID: $BACKEND_PID)${NC}"
        BACKEND_PID=""
    fi
    # 检查前端进程
    if [ -n "$FRONTEND_PID" ] && ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${YELLOW}⚠️  前端服务已停止 (PID: $FRONTEND_PID)${NC}"
        FRONTEND_PID=""
    fi
    # 如果所有服务都停止了，退出
    if [ -z "$BACKEND_PID" ] && [ -z "$FRONTEND_PID" ]; then
        echo -e "${YELLOW}所有服务已停止，脚本退出${NC}"
        exit 0
    fi
done
