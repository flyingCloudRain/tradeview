# 检查 CloudBase HTTP 访问服务配置

## 问题症状

- `ERR_FAILED` 错误
- CORS 错误：`No 'Access-Control-Allow-Origin' header is present`
- 请求似乎没有到达云函数

## 检查步骤

### 1. 检查 HTTP 访问服务配置

访问 CloudBase 控制台：
```
https://console.cloud.tencent.com/tcb/service?envId=trade-view-0gtiozig72c07cd0
```

### 2. 确认路径配置

HTTP 访问服务应该配置为：

**路径配置**：
- **前端路径**：`/trading-api/*`
- **后端路径**：`/*`（去掉 `/trading-api` 前缀）
- **云函数**：`trading-api`
- **方法**：`GET, POST, PUT, DELETE, OPTIONS`

或者：

- **前端路径**：`/trading-api/api/v1/*`
- **后端路径**：`/api/v1/*`
- **云函数**：`trading-api`
- **方法**：`GET, POST, PUT, DELETE, OPTIONS`

### 3. 检查 CORS 配置

在 HTTP 访问服务中，确保：
- ✅ 启用了 CORS
- ✅ 允许的源包含：`https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com`
- ✅ 允许的方法：`GET, POST, PUT, DELETE, OPTIONS`
- ✅ 允许的头部：`*` 或包含 `Content-Type`, `Authorization` 等

### 4. 测试步骤

1. **测试健康检查端点**：
   ```bash
   curl -v https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/health
   ```

2. **测试 API 端点（带 CORS 头）**：
   ```bash
   curl -X GET \
     -H "Origin: https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com" \
     -H "Access-Control-Request-Method: GET" \
     -v \
     https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/index/?date=2025-01-10
   ```

3. **检查响应头**：
   应该看到：
   ```
   < Access-Control-Allow-Origin: https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com
   < Access-Control-Allow-Credentials: true
   ```

## 如果仍然失败

### 方案 1: 使用 CloudBase CLI 检查配置

```bash
tcb service list --config-file cloudbaserc.json
```

### 方案 2: 检查云函数日志

在 CloudBase 控制台查看云函数日志：
```
https://console.cloud.tencent.com/tcb/scf?envId=trade-view-0gtiozig72c07cd0
```

查看是否有请求到达云函数。

### 方案 3: 重新创建 HTTP 访问服务

如果配置有问题，可以：
1. 删除现有的 HTTP 访问服务配置
2. 重新创建，确保路径映射正确

## 当前代码修复

已更新的代码包括：
1. ✅ 云函数入口处理路径前缀
2. ✅ 添加 OPTIONS 请求处理
3. ✅ 确保所有响应包含 CORS 头
4. ✅ 添加调试日志

## 下一步

1. 检查 CloudBase 控制台的 HTTP 访问服务配置
2. 确认路径映射正确
3. 测试 API 调用
4. 查看云函数日志确认请求是否到达
