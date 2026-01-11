# deploy.sh 使用指南

## 快速开始

### 1. 前置条件

在运行部署脚本之前，请确保：

#### 1.1 安装 CloudBase CLI

```bash
npm install -g @cloudbase/cli
```

#### 1.2 登录 CloudBase

```bash
cloudbase login
```

这会打开浏览器让你登录腾讯云账号。

#### 1.3 配置环境 ID

确保以下配置文件中的 `envId` 正确：

- `cloudbaserc.json` - 根目录配置文件
- `functions/trading-api/cloudbase.json` - 云函数配置文件

当前环境 ID: `trade-view-0gtiozig72c07cd0`

#### 1.4 配置前端环境变量（可选但推荐）

创建 `frontend/.env.production` 文件：

```env
VITE_API_BASE_URL=https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
```

#### 1.5 配置后端环境变量

在 CloudBase 控制台或使用 CLI 配置云函数环境变量：

```bash
# 数据库配置
cloudbase env:set DATABASE_URL "postgresql://user:password@host:port/database"

# Supabase 配置（如果使用）
cloudbase env:set SUPABASE_URL "https://your-project.supabase.co"
cloudbase env:set SUPABASE_KEY "your-supabase-anon-key"

# CORS 配置
cloudbase env:set CORS_ORIGINS '["https://your-domain.com"]'
```

### 2. 运行部署脚本

#### 2.1 确保脚本有执行权限

```bash
chmod +x deploy.sh
```

（脚本已经有执行权限，通常不需要这一步）

#### 2.2 执行部署

```bash
./deploy.sh
```

或者：

```bash
bash deploy.sh
```

## 脚本执行流程

脚本会自动执行以下步骤：

### 步骤 1: 构建前端项目

1. 检查 `frontend/node_modules` 是否存在
   - 如果不存在，自动运行 `npm install`
2. 运行 `npm run build` 构建前端
3. 验证 `frontend/dist` 目录是否创建成功

### 步骤 2: 部署后端云函数

1. 检查 `functions/trading-api` 目录是否存在
   - 如果不存在，自动创建
2. 同步后端代码到 `functions/trading-api`：
   - 复制 `backend/index.py`
   - 复制 `backend/requirements.txt`
   - 复制 `backend/app/` 目录
3. 检查并添加 `mangum` 依赖（如果缺失）
4. 部署云函数：`cloudbase functions:deploy trading-api`

### 步骤 3: 部署前端静态网站

1. 检查 `frontend/dist` 目录是否存在
   - 如果不存在，尝试重新构建
2. 部署静态网站：`cloudbase hosting:deploy frontend/dist`

## 部署后的访问地址

部署成功后，你可以通过以下地址访问：

1. **云函数 API 地址**:
   ```
   https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api
   ```

2. **静态网站地址**:
   ```
   https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com
   ```

## 常见问题

### Q1: 提示 "未安装 CloudBase CLI"

**解决方案**:
```bash
npm install -g @cloudbase/cli
```

### Q2: 提示 "请先登录 CloudBase"

**解决方案**:
```bash
cloudbase login
```

### Q3: 前端构建失败

**可能原因**:
- 依赖未安装
- TypeScript 类型错误
- 构建配置问题

**解决方案**:
```bash
cd frontend
npm install
npm run build
```

### Q4: 云函数部署失败

**可能原因**:
- 环境 ID 配置错误
- 函数代码有语法错误
- 依赖安装失败

**解决方案**:
1. 检查 `cloudbaserc.json` 和 `functions/trading-api/cloudbase.json` 中的 `envId`
2. 检查 Python 代码是否有语法错误
3. 查看 CloudBase 控制台的错误日志

### Q5: 前端部署失败

**可能原因**:
- `dist` 目录不存在
- 路径配置错误

**解决方案**:
脚本会自动尝试重新构建，如果仍然失败，手动构建：
```bash
cd frontend
npm run build
```

## 手动部署（如果脚本失败）

如果脚本执行失败，可以手动执行各个步骤：

### 1. 构建前端

```bash
cd frontend
npm install  # 如果需要
npm run build
cd ..
```

### 2. 部署云函数

```bash
# 同步代码
mkdir -p functions/trading-api
cp backend/index.py functions/trading-api/
cp backend/requirements.txt functions/trading-api/
cp -r backend/app functions/trading-api/

# 部署
cloudbase functions:deploy trading-api
```

### 3. 部署前端

```bash
cloudbase hosting:deploy frontend/dist
```

## 更新部署

如果代码有更新，直接重新运行脚本即可：

```bash
./deploy.sh
```

脚本会自动：
- 重新构建前端
- 同步最新的后端代码
- 重新部署云函数和前端

## 注意事项

1. **首次部署前**：确保已运行数据库迁移（如果使用数据库）
2. **环境变量**：确保在 CloudBase 控制台配置了必要的环境变量
3. **CORS 配置**：确保前端域名已添加到 CORS 允许列表中
4. **费用**：注意 CloudBase 的计费情况，避免产生意外费用
5. **日志查看**：部署后可以通过 CloudBase 控制台查看云函数日志

## 查看日志

```bash
# 查看云函数日志
cloudbase functions:log trading-api

# 查看实时日志
cloudbase functions:log trading-api --tail
```

## 回滚（如果需要）

如果需要回滚到之前的版本：

1. 在 CloudBase 控制台找到之前的函数版本
2. 选择回滚到该版本
3. 或者重新部署之前的代码
