# 修复 CORS 错误

## 问题描述

访问前端网站时，API 请求被 CORS 策略阻止：
```
Access to XMLHttpRequest at 'https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/...' 
from origin 'https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## 原因

后端的 CORS 配置中没有包含 CloudBase 前端域名。

## 解决方案

### 方案 1: 已更新代码（推荐）

已更新 `backend/app/config.py` 和 `functions/trading-api/app/config.py`，添加了 CloudBase 域名：

```python
CORS_ORIGINS: list = [
    # ... 本地开发地址 ...
    "https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com",
    "https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com",
]
```

**已重新部署云函数，配置应该已生效。**

### 方案 2: 通过环境变量配置（可选）

如果需要在 CloudBase 控制台配置，可以设置环境变量：

1. 访问 CloudBase 控制台：
   ```
   https://console.cloud.tencent.com/tcb/scf?envId=trade-view-0gtiozig72c07cd0
   ```

2. 进入云函数 `trading-api` → **函数配置** → **环境变量**

3. 添加环境变量：
   - **变量名**: `CORS_ORIGINS`
   - **变量值**: 
     ```json
     ["https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com", "https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com"]
     ```

4. 保存并等待配置生效

### 方案 3: 使用 CLI 配置环境变量

```bash
cloudbase env:set CORS_ORIGINS '["https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com", "https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com"]' -e trade-view-0gtiozig72c07cd0
```

## 验证

部署完成后，等待几分钟让配置生效，然后：

1. 刷新前端页面
2. 打开浏览器开发者工具（F12）
3. 检查 Network 标签，API 请求应该不再有 CORS 错误
4. 检查响应头应该包含：
   ```
   Access-Control-Allow-Origin: https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com
   ```

## 当前配置的前端域名

- `https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com`
- `https://trade-view-0gtiozig72c07cd0-1306563949.tcloudbaseapp.com`

## 注意事项

1. 如果添加了自定义域名，记得也要添加到 CORS_ORIGINS
2. 配置更改后需要重新部署云函数才能生效
3. 如果仍有问题，检查云函数日志：
   ```bash
   tcb fn log trading-api
   ```
