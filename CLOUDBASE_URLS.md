# CloudBase 访问地址

## 环境信息

- **环境 ID**: `trade-view-0gtiozig72c07cd0`
- **环境名称**: `trade-view`
- **环境状态**: `Normal`

## 访问地址

### 1. 云函数 API 地址

```
https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api
```

**API 端点示例**:
- 基础 URL: `https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api`
- API v1: `https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1`

### 2. 静态网站地址

```
https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com
```

### 3. 自定义域名（如果已配置）

在 CloudBase 控制台的"静态网站托管"中查看自定义域名配置。

## 前端环境变量配置

在 `frontend/.env.production` 中配置：

```env
VITE_API_BASE_URL=https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1
```

## 测试访问

### 测试云函数

```bash
# 测试健康检查端点（如果存在）
curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/health

# 测试 API 端点
curl https://trade-view-0gtiozig72c07cd0.ap-shanghai.app.tcloudbase.com/trading-api/api/v1/health
```

### 测试静态网站

在浏览器中访问：
```
https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com
```

## 控制台链接

- **CloudBase 控制台**: https://console.cloud.tencent.com/tcb
- **环境管理**: https://console.cloud.tencent.com/tcb/env/index?envId=trade-view-0gtiozig72c07cd0
- **云函数管理**: https://console.cloud.tencent.com/tcb/scf/index?envId=trade-view-0gtiozig72c07cd0
- **静态网站托管**: https://console.cloud.tencent.com/tcb/hosting/index?envId=trade-view-0gtiozig72c07cd0

## 注意事项

1. 确保云函数已部署并正常运行
2. 确保静态网站已部署
3. 检查 CORS 配置，确保前端域名被允许
4. 检查环境变量配置（数据库连接等）
5. 如果使用自定义域名，需要在控制台配置域名绑定
