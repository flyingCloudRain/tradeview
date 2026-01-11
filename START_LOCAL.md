# 本地开发环境启动指南

## ✅ 服务已启动

前端和后端服务已成功启动！

## 📋 服务地址

### 后端服务 (FastAPI)
- **API 地址**: http://localhost:8000
- **API 文档 (Swagger)**: http://localhost:8000/docs
- **API 文档 (ReDoc)**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

### 前端服务 (Vue + Vite)
- **前端应用**: http://localhost:3000
- **开发服务器**: 支持热重载

## 🚀 启动方式

### 方式一：使用启动脚本（推荐）

```bash
./scripts/start_dev.sh
```

脚本会自动：
- 检查依赖
- 启动后端服务（端口 8000）
- 启动前端服务（端口 3000）
- 显示服务状态和日志位置

### 方式二：手动启动

#### 启动后端

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

#### 启动前端（新终端）

```bash
cd frontend
npm run dev
```

## 🛑 停止服务

### 如果使用启动脚本
- 按 `Ctrl+C` 停止所有服务

### 如果手动启动
- 在每个终端按 `Ctrl+C` 停止对应服务

### 查找并停止进程

```bash
# 查找进程
ps aux | grep -E "(uvicorn|vite)" | grep -v grep

# 停止后端
pkill -f "uvicorn app.main:app"

# 停止前端
pkill -f "vite"
```

## 📝 日志文件

如果使用启动脚本，日志文件位于：
- `logs/backend.log` - 后端日志
- `logs/frontend.log` - 前端日志

查看日志：
```bash
# 查看后端日志
tail -f logs/backend.log

# 查看前端日志
tail -f logs/frontend.log
```

## 🔧 配置说明

### 后端配置

后端需要配置数据库连接，设置环境变量：
```bash
export DATABASE_URL="postgresql://user:password@host:5432/dbname"
```

### 前端配置

前端 API 代理配置在 `frontend/vite.config.ts`：
- 开发环境自动代理 `/api` 请求到 `http://localhost:8000`

如需修改 API 地址，创建 `frontend/.env.development`：
```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## 🐛 常见问题

### 问题 1: 端口被占用

**错误**: `Address already in use`

**解决方案**:
```bash
# 查找占用端口的进程
lsof -i :8000  # 后端端口
lsof -i :3000  # 前端端口

# 停止进程
kill -9 <PID>
```

### 问题 2: 后端启动失败

**可能原因**:
- 缺少依赖
- 数据库连接失败

**解决方案**:
```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 检查数据库配置
echo $DATABASE_URL
```

### 问题 3: 前端启动失败

**可能原因**:
- 缺少 node_modules
- 端口被占用

**解决方案**:
```bash
# 安装依赖
cd frontend
npm install

# 使用其他端口
npm run dev -- --port 3001
```

### 问题 4: CORS 错误

**错误**: `Access to XMLHttpRequest has been blocked by CORS policy`

**解决方案**:
- 确保后端 CORS 配置包含 `http://localhost:3000`
- 检查 `backend/app/config.py` 中的 `CORS_ORIGINS` 配置

## 📚 相关文档

- [后端 README](./backend/README.md)
- [前端 README](./frontend/README.md)
- [API 文档](http://localhost:8000/docs)

## 🎯 下一步

1. ✅ 服务已启动
2. 🔄 访问前端应用：http://localhost:3000
3. 🔄 查看 API 文档：http://localhost:8000/docs
4. 🔄 开始开发！
