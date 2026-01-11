# GitHub Secrets 配置指南

## ✅ 服务账号已配置完成

服务账号和权限已成功设置。现在需要将密钥配置到 GitHub Secrets。

## 📋 需要配置的 GitHub Secrets

访问你的 GitHub 仓库设置页面：
```
https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions
```

### Secret 1: GCP_PROJECT_ID

- **Secret 名称**: `GCP_PROJECT_ID`
- **Secret 值**: `tradeview-484009`

### Secret 2: GCP_SA_KEY

- **Secret 名称**: `GCP_SA_KEY`
- **Secret 值**: 复制 `gcp-sa-key.json` 文件的完整内容（见下方）

## 🔑 密钥文件内容

密钥文件位置：`gcp-sa-key.json`

**⚠️ 重要提示**：
- 密钥文件包含敏感信息，请妥善保管
- 配置完 GitHub Secrets 后，建议删除本地密钥文件
- 不要将密钥文件提交到 Git 仓库

## 📝 配置步骤

1. **访问 GitHub Secrets 页面**
   - 进入仓库 → Settings → Secrets and variables → Actions
   - 点击 "New repository secret"

2. **添加 GCP_PROJECT_ID**
   - Name: `GCP_PROJECT_ID`
   - Secret: `tradeview-484009`
   - 点击 "Add secret"

3. **添加 GCP_SA_KEY**
   - Name: `GCP_SA_KEY`
   - Secret: 复制 `gcp-sa-key.json` 文件的完整 JSON 内容
   - 点击 "Add secret"

4. **（可选）添加其他 Secrets**
   
   如果需要数据库迁移等功能，可以添加：
   
   - `DATABASE_URL`: 数据库连接字符串
   - `SUPABASE_URL`: Supabase 项目 URL
   - `SUPABASE_KEY`: Supabase API Key
   - `SUPABASE_SERVICE_KEY`: Supabase Service Key
   - `CORS_ORIGINS`: CORS 允许的前端 URL（JSON 数组格式）

## ✅ 验证配置

配置完成后，可以：

1. **推送代码触发部署**：
   ```bash
   git add .
   git commit -m "Configure auto deployment"
   git push origin main
   ```

2. **查看部署状态**：
   - 访问 GitHub → Actions 标签页
   - 查看 workflow 运行状态

3. **手动触发部署**：
   - 在 Actions 页面点击 "Deploy to Google Cloud Platform"
   - 点击 "Run workflow"

## 🔒 安全建议

配置完成后，删除本地密钥文件：

```bash
rm gcp-sa-key.json
```

或者将其添加到 `.gitignore`：

```bash
echo "gcp-sa-key.json" >> .gitignore
```

## 📚 相关文档

- [完整配置指南](./AUTO_DEPLOY_GCP.md)
- [快速设置指南](./GITHUB_ACTIONS_SETUP.md)
- [故障排查指南](./TROUBLESHOOTING_GCP.md)
