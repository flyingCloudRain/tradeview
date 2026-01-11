# 腾讯云 CloudBase 部署指南

## 快速开始

### 1. 安装 CloudBase CLI

```bash
npm install -g @cloudbase/cli
```

### 2. 登录腾讯云

```bash
cloudbase login
```

### 3. 配置环境 ID

修改以下文件中的 `your-env-id` 为你的实际环境 ID：
- `backend/cloudbase.json`
- `cloudbaserc.json`

### 4. 配置前端环境变量

创建 `frontend/.env.production`：

```env
VITE_API_BASE_URL=https://your-env-id.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
```

### 5. 一键部署

```bash
./deploy.sh
```

## 部署架构

- **后端**: 腾讯云 CloudBase 云函数（Python 3.9）
- **前端**: 腾讯云 CloudBase 静态网站托管
- **数据库**: 外部数据库（PostgreSQL/Supabase）

## 详细文档

完整部署文档请查看：[cloudbase-deploy.md](./cloudbase-deploy.md)

## 重要提示

1. 首次部署前需要配置环境变量（数据库连接等）
2. 需要运行数据库迁移脚本
3. 确保 CORS 配置包含前端域名
