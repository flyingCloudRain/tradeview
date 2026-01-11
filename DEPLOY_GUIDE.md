# CloudBase 部署指南

## 快速部署

### 一键部署（推荐）

```bash
./deploy.sh
```

## 部署前检查清单

### ✅ 前置条件

- [x] CloudBase CLI 已安装
- [x] 已登录 CloudBase (`tcb login` 或 `cloudbase login`)
- [x] 环境 ID 已配置 (`trade-view-0gtiozig72c07cd0`)
- [x] 前端环境变量已配置 (`frontend/.env.production`)
- [ ] 数据库迁移已完成（首次部署必须）
- [ ] 后端环境变量已配置（DATABASE_URL 等）

### 📋 部署步骤

部署脚本会自动执行以下步骤：

1. **构建前端项目**
   - 检查并安装依赖
   - 运行 `npm run build`
   - 生成 `frontend/dist` 目录

2. **部署后端云函数**
   - 同步代码到 `functions/trading-api`
   - 部署 `trading-api` 云函数

3. **部署前端静态网站**
   - 部署 `frontend/dist` 到静态网站托管

## 详细部署步骤

### 步骤 1: 检查前置条件

```bash
# 1. 确认在项目根目录
cd /Users/bigdan/Documents/2025/trade/trading_review_new

# 2. 检查 CloudBase CLI
cloudbase --version
# 或
tcb --version

# 3. 检查登录状态
tcb env list
# 应该能看到 trade-view 环境

# 4. 检查配置文件
cat cloudbaserc.json | grep envId
# 应该显示: "envId": "trade-view-0gtiozig72c07cd0"
```

### 步骤 2: 配置环境变量（如果未配置）

#### 后端环境变量（在 CloudBase 控制台配置）

```bash
# 方式 1: 使用 CLI 配置
cloudbase env:set DATABASE_URL "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"
cloudbase env:set SUPABASE_URL "https://xxx.supabase.co"
cloudbase env:set SUPABASE_KEY "your-supabase-key"

# 方式 2: 在 CloudBase 控制台配置
# 访问: https://console.cloud.tencent.com/tcb/scf/index?envId=trade-view-0gtiozig72c07cd0
# 进入"函数配置" -> "环境变量"
```

#### 前端环境变量（已自动配置）

文件 `frontend/.env.production` 已创建，包含：
```env
VITE_API_BASE_URL=https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
```

### 步骤 3: 运行数据库迁移（首次部署必须）

```bash
cd backend

# 设置数据库连接（如果使用 Supabase）
export DATABASE_URL="postgresql://postgres:password@db.xxx.supabase.co:5432/postgres"

# 运行迁移
alembic upgrade head

# 验证迁移
python scripts/verify_database.py
```

### 步骤 4: 执行部署

```bash
# 确保在项目根目录
cd /Users/bigdan/Documents/2025/trade/trading_review_new

# 运行部署脚本
./deploy.sh
```

或者手动执行：

```bash
# 1. 构建前端
cd frontend
npm install
npm run build
cd ..

# 2. 部署云函数
cloudbase functions:deploy trading-api -e trade-view-0gtiozig72c07cd0

# 3. 部署静态网站
cloudbase hosting:deploy frontend/dist -e trade-view-0gtiozig72c07cd0
```

## 部署后验证

### 1. 检查云函数状态

```bash
tcb fn list
# 或
cloudbase functions:list -e trade-view-0gtiozig72c07cd0
```

### 2. 测试 API 端点

```bash
# 测试健康检查（如果存在）
curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/health

# 测试其他端点
curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/lhb/
```

### 3. 访问前端网站

在浏览器中打开：
```
https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com
```

### 4. 查看日志

```bash
# 查看云函数日志
cloudbase functions:log trading-api -e trade-view-0gtiozig72c07cd0

# 或使用新命令
tcb fn log trading-api
```

## 常见问题

### Q1: 部署失败，提示 INVALID_ENV

**解决方案**:
1. 检查 `cloudbaserc.json` 中的环境 ID 是否正确
2. 重新登录: `tcb login`
3. 查看 `FIX_INVALID_ENV.md` 获取详细解决方案

### Q2: 前端构建失败

**解决方案**:
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

### Q3: 云函数部署失败

**解决方案**:
1. 检查 `functions/trading-api` 目录是否存在
2. 确认 `requirements.txt` 包含所有依赖
3. 查看详细错误日志

### Q4: API 请求失败（CORS 错误）

**解决方案**:
1. 检查后端 CORS 配置 (`backend/app/config.py`)
2. 确保前端域名在 `CORS_ORIGINS` 中
3. 检查环境变量配置

### Q5: 数据库连接失败

**解决方案**:
1. 检查 CloudBase 环境变量中的 `DATABASE_URL`
2. 确认数据库允许 CloudBase IP 访问
3. 验证数据库迁移是否完成

## 更新部署

如果代码有更新，重新运行部署脚本即可：

```bash
./deploy.sh
```

脚本会自动：
- 重新构建前端
- 同步最新代码
- 更新云函数
- 更新静态网站

## 访问地址

部署完成后，访问地址：

- **前端网站**: https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com
- **API 地址**: https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
- **控制台**: https://console.cloud.tencent.com/tcb/env/index?envId=trade-view-0gtiozig72c07cd0

## 相关文档

- `FIX_INVALID_ENV.md` - INVALID_ENV 错误修复指南
- `CLOUDBASE_URLS.md` - 访问地址详细说明
- `cloudbase-deploy.md` - 详细部署文档
