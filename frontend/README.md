# 交易复盘系统 - 前端

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### 3. 运行开发服务器

```bash
npm run dev
```

### 4. 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── api/          # API调用
│   ├── stores/       # Pinia状态管理
│   ├── router/       # 路由配置
│   ├── views/        # 页面组件
│   ├── components/   # 公共组件
│   └── utils/        # 工具函数
└── package.json
```

