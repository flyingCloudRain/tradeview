# 修复 API 400 错误和 CORS 问题

## 问题描述

1. **400 Bad Request**: API 请求返回 400 错误
2. **CORS 错误**: 缺少 `Access-Control-Allow-Origin` 头

## 可能的原因

### 1. API 网关路径配置问题

CloudBase 的 HTTP 访问服务可能没有正确配置路径映射。

**检查步骤**：
1. 访问 CloudBase 控制台
2. 进入 **HTTP 访问服务** 或 **API 网关**
3. 检查路径配置：
   - 路径前缀：`/trading-api`
   - 后端路径：`/` 或 `/api/v1`
   - 云函数：`trading-api`

### 2. 云函数路径处理

云函数接收的路径可能包含 `/trading-api` 前缀，但 FastAPI 应用期望的是 `/api/v1`。

## 解决方案

### 方案 1: 配置 API 网关路径重写（推荐）

在 CloudBase 控制台配置 HTTP 访问服务：

1. **路径配置**：
   - 前端路径：`/trading-api/*`
   - 后端路径：`/*`（去掉 `/trading-api` 前缀）
   - 云函数：`trading-api`

2. **或者**：
   - 前端路径：`/trading-api/api/v1/*`
   - 后端路径：`/api/v1/*`
   - 云函数：`trading-api`

### 方案 2: 在云函数中处理路径

修改 `functions/trading-api/index.py`，处理路径前缀：

```python
def main_handler(event, context):
    """云函数入口"""
    from mangum import Mangum
    
    # 处理路径前缀
    path = event.get("path", "/")
    # 如果路径以 /trading-api 开头，去掉它
    if path.startswith("/trading-api"):
        path = path[len("/trading-api"):]
        event["path"] = path
    
    handler = Mangum(app, lifespan="off")
    return handler(event, context)
```

### 方案 3: 使用根路径配置

如果可能，配置 API 网关使用根路径：

- 前端路径：`/api/v1/*`
- 后端路径：`/api/v1/*`
- 云函数：`trading-api`

然后更新前端 API 基础 URL：
```env
VITE_API_BASE_URL=https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/api/v1
```

## 当前配置

### CORS 配置（已更新）

已更新 CORS 配置，支持：
- 所有 `*.tcloudbaseapp.com` 子域名（通过正则表达式）
- 本地开发地址
- 精确匹配的 CloudBase 域名

### 云函数配置

- 函数名：`trading-api`
- 运行时：Python 3.9
- 入口：`index.main_handler`

## 验证步骤

1. **检查 API 网关配置**：
   ```
   访问: https://console.cloud.tencent.com/tcb/service?envId=trade-view-0gtiozig72c07cd0
   ```

2. **测试 API 端点**：
   ```bash
   # 测试根路径
   curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/
   
   # 测试健康检查
   curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/health
   
   # 测试 API v1
   curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/health
   ```

3. **检查 CORS 头**：
   ```bash
   curl -H "Origin: https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com" \
        -v https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/health
   ```

## 临时解决方案

如果问题持续，可以：

1. **直接访问云函数 URL**（如果 CloudBase 提供了）：
   - 检查云函数是否有直接的 HTTP 触发 URL
   - 更新前端 API 基础 URL

2. **使用代理**：
   - 在前端使用代理转发请求
   - 或使用 CloudBase 的静态网站代理功能

## 下一步

1. ✅ 已更新 CORS 配置（支持通配符域名）
2. ✅ 已重新部署云函数
3. ⏳ 需要检查 API 网关路径配置
4. ⏳ 可能需要调整路径映射

## 相关链接

- [CloudBase HTTP 访问服务文档](https://docs.cloudbase.net/service/intro)
- [CloudBase API 网关配置](https://console.cloud.tencent.com/tcb/service)
