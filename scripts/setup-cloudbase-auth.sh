#!/bin/bash

# CloudBase CLI 认证配置脚本
# 用于 CI/CD 环境中的非交互式登录

set -e

echo "配置 CloudBase CLI 认证..."

# 检查必需的环境变量
if [ -z "$TCB_SECRET_ID" ] || [ -z "$TCB_SECRET_KEY" ]; then
    echo "错误: 未设置 TCB_SECRET_ID 或 TCB_SECRET_KEY"
    exit 1
fi

# 创建 CloudBase 配置目录
mkdir -p ~/.tcb

# 方式 1: 创建登录配置文件（如果 CloudBase CLI 支持）
cat > ~/.tcb/config.json << EOF
{
  "secretId": "$TCB_SECRET_ID",
  "secretKey": "$TCB_SECRET_KEY"
}
EOF

echo "✅ 已创建 CloudBase 配置文件"

# 方式 2: 尝试使用环境变量（如果 CLI 支持）
export TCB_SECRET_ID="$TCB_SECRET_ID"
export TCB_SECRET_KEY="$TCB_SECRET_KEY"

echo "✅ 已设置环境变量"

# 注意：CloudBase CLI 的实际登录方式可能需要根据版本调整
# 如果上述方式不工作，可能需要：
# 1. 使用 cloudbase login --key
# 2. 或使用其他认证方式
# 3. 或预先在本地登录并导出认证信息

echo "请根据 CloudBase CLI 版本调整登录方式"
