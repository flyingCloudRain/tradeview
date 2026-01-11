# CI/CD 数据库自动迁移配置

## 概述

GitHub Actions 工作流已配置为在每次部署时自动运行数据库迁移，确保数据库结构与代码同步。

## 工作流中的迁移步骤

### 执行位置

数据库迁移在以下步骤之后、部署云函数之前执行：

1. ✅ 安装 Python 依赖
2. ✅ 配置 CloudBase 认证
3. ✅ **运行数据库迁移** ← 新增
4. ✅ 构建前端
5. ✅ 部署云函数

### 迁移步骤详情

```yaml
- name: Run Database Migrations
  working-directory: ./backend
  run: |
    # 检查 DATABASE_URL 是否配置
    # 检查当前数据库版本
    # 执行 alembic upgrade head
    # 验证迁移结果
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## GitHub Secrets 配置

### 必需配置

在 GitHub Secrets 中添加 `DATABASE_URL`：

**Secret 名称**: `DATABASE_URL`

**值格式**:
```
postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
```

**示例**:
```
postgresql://postgres:your_password@db.uvtmbjgndhcmlupridss.supabase.co:5432/postgres
```

### 配置步骤

1. 访问 GitHub Secrets 设置：
   ```
   https://github.com/flyingCloudRain/tradeview/settings/secrets/actions
   ```

2. 点击 **New repository secret**

3. 输入：
   - **Name**: `DATABASE_URL`
   - **Secret**: `postgresql://postgres:your_password@db.xxx.supabase.co:5432/postgres`

4. 点击 **Add secret**

## 迁移行为

### 自动执行

- ✅ 每次推送到 `main`/`master` 分支时自动运行
- ✅ 手动触发工作流时也会运行
- ✅ 自动执行所有待执行的迁移文件
- ✅ 按迁移文件顺序执行

### 错误处理

- ⚠️ 如果 `DATABASE_URL` 未配置，会跳过迁移步骤（警告但不失败）
- ❌ 如果迁移失败，整个部署流程会停止
- ✅ 迁移成功后会验证当前数据库版本

### 安全特性

- 🔒 数据库密码不会在日志中显示（自动隐藏）
- 🔒 连接字符串存储在 GitHub Secrets 中
- 🔒 迁移在部署前执行，确保数据库结构正确

## 迁移流程

1. **检查配置**: 验证 `DATABASE_URL` 是否设置
2. **检查版本**: 查看当前数据库迁移版本
3. **执行迁移**: 运行 `alembic upgrade head`
4. **验证结果**: 确认迁移成功并显示当前版本

## 日志输出示例

```
==========================================
运行数据库迁移
==========================================

数据库连接: postgresql://postgres@***

检查当前数据库版本...
7494e0e4dba5 (head)

执行数据库迁移...
INFO  [alembic.runtime.migration] Running upgrade ...
✅ 数据库迁移完成
```

## 注意事项

### 1. 首次部署

- 首次部署时，如果数据库为空，会执行所有迁移文件
- 确保 Supabase 数据库允许 GitHub Actions IP 访问

### 2. 迁移顺序

- Alembic 会自动按迁移文件的时间戳顺序执行
- 不需要手动指定顺序

### 3. 回滚

如果需要回滚迁移：

```bash
# 本地回滚
cd backend
alembic downgrade -1

# 或回滚到指定版本
alembic downgrade <revision>
```

### 4. 跳过迁移

如果不想在 CI/CD 中运行迁移：

- 不配置 `DATABASE_URL` Secret（会跳过迁移步骤）
- 或修改工作流，将 `continue-on-error` 设置为 `true`

## 验证迁移

### 在 GitHub Actions 中查看

1. 进入 Actions 页面
2. 查看最新的工作流运行
3. 展开 "Run Database Migrations" 步骤
4. 查看迁移日志

### 手动验证

```bash
# 查看当前数据库版本
cd backend
alembic current

# 查看迁移历史
alembic history

# 验证数据库结构
python scripts/verify_database.py
```

## 故障排查

### 问题 1: 迁移步骤被跳过

**原因**: `DATABASE_URL` 未配置

**解决方案**: 在 GitHub Secrets 中添加 `DATABASE_URL`

### 问题 2: 迁移失败

**可能原因**:
- 数据库连接字符串错误
- 数据库不允许 GitHub Actions IP 访问
- 迁移文件有错误

**解决方案**:
1. 检查 `DATABASE_URL` 是否正确
2. 在 Supabase 控制台检查数据库访问设置
3. 查看工作流日志定位具体错误

### 问题 3: 迁移超时

**解决方案**:
- 检查数据库连接是否正常
- 确认迁移文件没有长时间运行的 SQL

## 相关文档

- `backend/migrate-database.md` - 数据库迁移详细指南
- `GITHUB_CLOUDBASE_SETUP.md` - GitHub Actions 配置指南
- `GITHUB_SECRETS_QUICK.md` - Secrets 快速配置

## 当前配置状态

- ✅ 工作流已配置数据库迁移步骤
- ✅ 迁移在部署前自动执行
- ⏳ 需要在 GitHub Secrets 中配置 `DATABASE_URL`
