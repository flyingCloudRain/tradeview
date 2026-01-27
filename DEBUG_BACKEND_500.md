# 调试后端 500 错误

## 问题描述

访问 `https://trading-api-wwbrnphpuq-uc.a.run.app/health` 返回 500 错误。

## 已实施的修复

1. ✅ **改进健康检查端点**：添加了错误处理和详细日志
2. ✅ **路由注册保护**：即使路由注册失败，应用也能启动
3. ✅ **安全路由导入**：使用 `safe_include_router` 函数，单个路由失败不会导致整个应用失败

## 查看日志

### 方法一：通过 GCP Console 查看

1. 访问 [Cloud Functions Console](https://console.cloud.google.com/functions/list)
2. 选择项目：`tradeview-484009`
3. 点击函数：`trading-api`
4. 点击 "日志" 标签页
5. 查看最近的错误日志

### 方法二：使用 gcloud 命令查看

```bash
# 设置项目
gcloud config set project tradeview-484009

# 查看最近的日志
gcloud functions logs read trading-api \
  --gen2 \
  --region=us-central1 \
  --limit=50

# 查看错误日志
gcloud functions logs read trading-api \
  --gen2 \
  --region=us-central1 \
  --limit=50 \
  --filter="severity>=ERROR"
```

### 方法三：实时查看日志

```bash
gcloud functions logs tail trading-api \
  --gen2 \
  --region=us-central1
```

## 常见原因

### 1. 数据库连接问题

如果日志显示数据库连接错误：

```bash
# 检查环境变量是否设置
gcloud functions describe trading-api \
  --gen2 \
  --region=us-central1 \
  --format="value(serviceConfig.environmentVariables)"
```

### 2. 路由导入错误

如果日志显示导入错误，检查缺失的模块或依赖：

```bash
# 查看函数依赖
gcloud functions describe trading-api \
  --gen2 \
  --region=us-central1 \
  --format="value(buildConfig.runtime)"
```

### 3. 配置加载错误

检查配置是否正确加载：

```bash
# 查看环境变量
gcloud functions describe trading-api \
  --gen2 \
  --region=us-central1 \
  --format="get(serviceConfig.environmentVariables)"
```

## 测试健康检查端点

### 使用 curl

```bash
curl -v https://trading-api-wwbrnphpuq-uc.a.run.app/health
```

### 使用 Python

```python
import requests

response = requests.get("https://trading-api-wwbrnphpuq-uc.a.run.app/health")
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

## 重新部署

如果修复了代码，重新部署：

```bash
# 触发 GitHub Actions 部署
git commit --allow-empty -m "trigger redeploy"
git push

# 或手动部署
cd backend
gcloud functions deploy trading-api \
  --gen2 \
  --runtime=python311 \
  --region=us-central1 \
  --source=. \
  --entry-point=main \
  --trigger-http \
  --allow-unauthenticated
```

## 下一步

1. 查看 Cloud Functions 日志，找到具体的错误信息
2. 根据错误信息修复问题
3. 重新部署并验证
