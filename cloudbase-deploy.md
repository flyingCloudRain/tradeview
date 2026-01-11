# CloudBase 部署方案

## 一、准备工作

### 1. 安装 CloudBase CLI

```bash
npm install -g @cloudbase/cli
```

### 2. 登录 CloudBase

```bash
cloudbase login
```

### 3. 初始化项目

```bash
# 在项目根目录执行
cloudbase init
```

## 二、后端部署（云函数）

### 1. 创建云函数配置

在 `backend` 目录下已创建 `cloudbase.json`，需要修改 `envId` 为你的环境 ID。

### 2. 云函数入口文件

已创建 `backend/index.py` 作为云函数入口。

### 3. 更新 requirements.txt

已在 `backend/requirements.txt` 中添加 `mangum>=0.17.0`。

### 4. 部署云函数

```bash
cd backend
# 修改 cloudbase.json 中的 envId
cloudbase functions:deploy trading-api
```

## 三、前端部署（静态网站托管）

### 1. 构建前端项目

```bash
cd frontend
npm install
npm run build
```

### 2. 配置环境变量

创建 `frontend/.env.production`：

```env
VITE_API_BASE_URL=https://your-env-id.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
```

**注意**：将 `your-env-id` 替换为你的 CloudBase 环境 ID。

### 3. 部署前端

```bash
# 方式一：使用 CLI 部署
cloudbase hosting:deploy frontend/dist -e your-env-id

# 方式二：使用配置文件（需要先修改 cloudbaserc.json 中的 envId）
cloudbase hosting:deploy
```

## 四、数据库配置

### 1. 使用 CloudBase 数据库

在 CloudBase 控制台创建数据库，然后配置环境变量：

```bash
cloudbase env:set DATABASE_URL postgresql://user:password@host:port/database
```

### 2. 或使用外部数据库

如果使用 Supabase 或其他外部数据库，配置相应的连接字符串。

## 五、环境变量配置

### 在 CloudBase 控制台配置环境变量

进入云函数配置，添加以下环境变量：

- `DATABASE_URL`: 数据库连接字符串
- `SUPABASE_URL`: Supabase URL（如果使用）
- `SUPABASE_KEY`: Supabase Key（如果使用）
- `CORS_ORIGINS`: CORS 允许的源，格式：`["https://your-domain.com"]`

### 或使用 CLI 配置

```bash
cloudbase env:set DATABASE_URL your-database-url
cloudbase env:set SUPABASE_URL your-supabase-url
cloudbase env:set SUPABASE_KEY your-supabase-key
cloudbase env:set CORS_ORIGINS '["https://your-domain.com"]'
```

## 六、API 网关配置（可选）

如果需要自定义域名，可以配置 API 网关：

1. 在 CloudBase 控制台创建 API 网关
2. 将云函数绑定到 API 网关
3. 配置自定义域名

## 七、一键部署脚本

已创建 `deploy.sh` 脚本，使用方法：

```bash
# 1. 给脚本添加执行权限（已自动添加）
chmod +x deploy.sh

# 2. 修改配置文件中的 envId
# - backend/cloudbase.json
# - cloudbaserc.json

# 3. 执行部署
./deploy.sh
```

## 八、数据库迁移（重要）

### Supabase 数据库迁移

**必须运行数据库迁移**来创建表结构。有两种方式：

#### 方式一：部署前本地迁移（推荐）

```bash
cd backend

# 配置 Supabase 数据库连接
export DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres"

# 运行迁移
alembic upgrade head

# 验证迁移
python scripts/verify_database.py
```

#### 方式二：创建迁移云函数

可以创建一个独立的迁移云函数，需要时手动触发。

详细迁移说明请查看：[backend/migrate-database.md](./backend/migrate-database.md)

## 九、注意事项

1. **CORS 配置**：确保在 `backend/app/config.py` 中配置正确的前端域名
2. **数据库迁移**：**首次部署必须运行数据库迁移脚本**（见上方说明）
3. **文件上传**：如果需要文件上传功能，需要配置云存储
4. **定时任务**：云函数不支持长期运行的定时任务，需要使用 CloudBase 的定时触发器
5. **环境 ID**：记得在所有配置文件中替换 `your-env-id` 为实际的环境 ID
6. **环境变量**：确保在 CloudBase 控制台配置了 `DATABASE_URL` 环境变量

## 九、监控和日志

1. 在 CloudBase 控制台查看云函数日志
2. 使用 CLI 查看日志：`cloudbase functions:log trading-api`
3. 配置告警规则
4. 监控函数执行情况

## 十一、快速部署步骤

### 1. 一键部署（推荐）

```bash
# 1. 修改配置文件中的 envId
# - backend/cloudbase.json 中的 "envId"
# - cloudbaserc.json 中的 "envId"

# 2. 配置前端环境变量
# 创建 frontend/.env.production，设置 VITE_API_BASE_URL

# 3. 执行部署脚本
./deploy.sh
```

### 2. 手动部署

```bash
# 1. 安装 CloudBase CLI
npm install -g @cloudbase/cli

# 2. 登录
cloudbase login

# 3. 初始化（首次部署）
cloudbase init

# 4. 构建前端
cd frontend
npm install
npm run build
cd ..

# 5. 部署后端
cd backend
cloudbase functions:deploy trading-api
cd ..

# 6. 部署前端
cloudbase hosting:deploy frontend/dist
```

## 十二、环境变量配置

### 前端环境变量

创建 `frontend/.env.production`：

```env
VITE_API_BASE_URL=https://your-env-id.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
```

### 后端环境变量

在 CloudBase 控制台或使用 CLI 配置：

```bash
# 数据库配置
cloudbase env:set DATABASE_URL postgresql://user:password@host:port/database

# Supabase 配置（如果使用）
cloudbase env:set SUPABASE_URL https://your-project.supabase.co
cloudbase env:set SUPABASE_KEY your-supabase-anon-key

# CORS 配置
cloudbase env:set CORS_ORIGINS '["https://your-domain.com"]'
```

## 十三、成本优化建议

1. 使用云函数按量计费
2. 配置合理的超时时间和内存大小（当前：60秒，512MB）
3. 使用 CDN 加速静态资源
4. 数据库连接池优化
5. 启用云函数冷启动优化

## 十四、常见问题

### Q1: 云函数超时怎么办？
A: 增加超时时间或优化代码性能，在 `cloudbase.json` 中调整 `timeout` 值。

### Q2: 如何查看日志？
A: 在 CloudBase 控制台的云函数日志中查看，或使用 `tcb fn log trading-api`。

### Q3: 数据库连接失败？
A: 检查环境变量中的 `DATABASE_URL` 是否正确，确保数据库允许 CloudBase 的 IP 访问。

### Q4: CORS 错误？
A: 在 `backend/app/config.py` 中更新 `CORS_ORIGINS`，包含前端域名。

### Q5: 如何获取环境 ID？
A: 登录 CloudBase 控制台，在环境列表中可以看到环境 ID。

## 十五、更新部署

```bash
# 重新部署后端
cd backend
cloudbase functions:deploy trading-api

# 重新部署前端
cd frontend
npm run build
cd ..
cloudbase hosting:deploy frontend/dist
```

## 十六、文件结构说明

```
项目根目录/
├── backend/
│   ├── index.py              # 云函数入口文件（新增）
│   ├── cloudbase.json        # 云函数配置（新增）
│   ├── .tcbignore           # 云函数忽略文件（新增）
│   └── requirements.txt     # 已添加 mangum
├── frontend/
│   └── .env.production      # 生产环境配置（需创建）
├── cloudbaserc.json         # CloudBase 配置文件（新增）
├── deploy.sh                # 一键部署脚本（新增）
└── cloudbase-deploy.md      # 部署文档（本文件）
```

## 十七、部署检查清单

- [ ] 安装 CloudBase CLI
- [ ] 登录 CloudBase (`cloudbase login`)
- [ ] 修改 `backend/cloudbase.json` 中的 `envId`
- [ ] 修改 `cloudbaserc.json` 中的 `envId`
- [ ] 创建 `frontend/.env.production` 并配置 API 地址
- [ ] 配置后端环境变量（数据库、Supabase 等）
- [ ] **运行数据库迁移（首次部署必须）** - 见"数据库迁移"章节
- [ ] 执行部署脚本或手动部署
- [ ] 验证前端和后端是否正常访问
