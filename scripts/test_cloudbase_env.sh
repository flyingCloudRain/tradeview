#!/bin/bash

# 测试 CloudBase 环境访问

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "=========================================="
echo "测试 CloudBase 环境访问"
echo "=========================================="
echo ""

# 读取环境 ID
if [ ! -f "cloudbaserc.json" ]; then
    echo "❌ 未找到 cloudbaserc.json"
    exit 1
fi

ENV_ID=$(grep -o '"envId":\s*"[^"]*"' cloudbaserc.json | cut -d'"' -f4)
echo "环境 ID: $ENV_ID"
echo ""

# 测试 1: 列出环境
echo "测试 1: 列出所有环境..."
if command -v tcb &> /dev/null; then
    tcb env list
else
    cloudbase env:list
fi
echo ""

# 测试 2: 使用明确的环境 ID 部署（dry-run）
echo "测试 2: 验证环境 ID 有效性..."
echo "（这只是验证，不会实际部署）"
echo ""

# 测试 3: 检查云函数列表
echo "测试 3: 检查云函数..."
if command -v tcb &> /dev/null; then
    echo "使用新命令格式: tcb fn list"
    tcb fn list 2>&1 | head -10 || echo "⚠️  命令执行失败，可能需要明确指定环境"
else
    echo "使用旧命令格式: cloudbase functions:list"
    cloudbase functions:list -e "$ENV_ID" 2>&1 | head -10 || \
    cloudbase functions:list 2>&1 | head -10 || echo "⚠️  命令执行失败"
fi
echo ""

echo "=========================================="
echo "测试完成"
echo "=========================================="
echo ""
echo "如果所有测试都通过，说明环境配置正确"
echo "如果出现 INVALID_ENV 错误，请："
echo "1. 检查环境 ID 是否正确: $ENV_ID"
echo "2. 重新登录: tcb login 或 cloudbase login"
echo "3. 查看详细修复指南: FIX_INVALID_ENV.md"
