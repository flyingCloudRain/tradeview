# 修复 HTTP 418 错误

## 问题描述

访问 `https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com/` 时返回 HTTP 418 错误（"I'm a teapot"）。

## 原因分析

HTTP 418 错误通常出现在以下情况：
1. CloudBase 静态网站托管未正确配置默认文档
2. SPA（单页应用）路由需要重写规则
3. 根目录 `/` 无法正确映射到 `index.html`

## 解决方案

### 方案 1: 在 CloudBase 控制台配置重写规则（推荐）

1. 登录 [CloudBase 控制台](https://console.cloud.tencent.com/tcb)
2. 选择环境：`trade-view-0gtiozig72c07cd0`
3. 进入 **静态网站托管** → **基础配置**
4. 配置重写规则：
   - 匹配规则: `.*`
   - 重写到: `/index.html`
5. 保存配置

### 方案 2: 使用 CLI 配置（如果支持）

```bash
# 尝试使用 CLI 配置重写规则
tcb hosting:config set rewriteRules '[{"match": ".*", "to": "/index.html"}]' -e trade-view-0gtiozig72c07cd0
```

### 方案 3: 直接访问 index.html

临时解决方案：直接访问完整路径：
```
https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com/index.html
```

### 方案 4: 检查部署配置

确保 `cloudbaserc.json` 中包含重写规则配置：

```json
{
  "hosting": {
    "type": "static",
    "cloudPath": "/",
    "rewriteRules": [
      {
        "match": ".*",
        "to": "/index.html"
      }
    ]
  }
}
```

## 验证步骤

1. 配置重写规则后，等待几分钟让配置生效
2. 访问根目录：`https://trade-view-0gtiozig72c07cd0.tcloudbaseapp.com/`
3. 应该能正常加载页面，而不是返回 418 错误

## 当前状态

- ✅ `index.html` 文件已正确部署
- ✅ 静态资源文件已上传
- ⚠️ 需要配置重写规则以支持 SPA 路由

## 相关链接

- [CloudBase 静态网站托管文档](https://docs.cloudbase.net/hosting/intro)
- [CloudBase 控制台](https://console.cloud.tencent.com/tcb/hosting?envId=trade-view-0gtiozig72c07cd0)
