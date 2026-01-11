#!/bin/bash

# CloudBase 环境诊断脚本

set -e

echo "=========================================="
echo "CloudBase 环境诊断"
echo "=========================================="
echo ""

# 1. 检查 CLI 是否安装
echo "1. 检查 CloudBase CLI..."
if command -v cloudbase &> /dev/null; then
    echo "   ✅ CloudBase CLI 已安装"
    cloudbase --version 2>&1 | head -1
else
    echo "   ❌ CloudBase CLI 未安装"
    echo "   请运行: npm install -g @cloudbase/cli"
    exit 1
fi
echo ""

# 2. 检查登录状态
echo "2. 检查登录状态..."
if cloudbase whoami &> /dev/null; then
    echo "   ✅ 已登录"
    cloudbase whoami
else
    echo "   ❌ 未登录"
    echo "   请运行: cloudbase login"
    exit 1
fi
echo ""

# 3. 列出所有环境
echo "3. 列出所有可用环境..."
tcb env list 2>&1 | grep -A 10 "Environment ID" || cloudbase env:list 2>&1 | grep -A 10 "Environment ID"
echo ""

# 4. 检查配置文件中的环境 ID
echo "4. 检查配置文件..."
ENV_ID="trade-view-0gtiozig72c07cd0"

echo "   配置文件中的环境 ID: $ENV_ID"
echo ""

# 检查各个配置文件
echo "   检查 cloudbaserc.json..."
if grep -q "$ENV_ID" cloudbaserc.json 2>/dev/null; then
    echo "   ✅ cloudbaserc.json 包含环境 ID"
else
    echo "   ❌ cloudbaserc.json 中未找到环境 ID"
fi

echo "   检查 backend/cloudbase.json..."
if [ -f "backend/cloudbase.json" ] && grep -q "$ENV_ID" backend/cloudbase.json 2>/dev/null; then
    echo "   ✅ backend/cloudbase.json 包含环境 ID"
else
    echo "   ⚠️  backend/cloudbase.json 中未找到环境 ID 或文件不存在"
fi

echo "   检查 functions/trading-api/cloudbase.json..."
if [ -f "functions/trading-api/cloudbase.json" ] && grep -q "$ENV_ID" functions/trading-api/cloudbase.json 2>/dev/null; then
    echo "   ✅ functions/trading-api/cloudbase.json 包含环境 ID"
else
    echo "   ⚠️  functions/trading-api/cloudbase.json 中未找到环境 ID 或文件不存在"
fi
echo ""

# 5. 测试环境访问
echo "5. 测试环境访问..."
echo "   尝试获取环境信息..."

# 使用新命令格式
if tcb env:get --env-id "$ENV_ID" 2>&1 | head -5; then
    echo "   ✅ 环境访问正常"
else
    echo "   ⚠️  使用新命令格式失败，尝试旧格式..."
    if cloudbase env:get DATABASE_URL 2>&1 | head -5; then
        echo "   ✅ 使用旧命令格式访问正常"
    else
        echo "   ❌ 环境访问失败，可能的原因："
        echo "      - 环境 ID 不正确"
        echo "      - 当前账号没有访问权限"
        echo "      - 环境已被删除或暂停"
    fi
fi
echo ""

# 6. 建议
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果遇到 INVALID_ENV 错误，请尝试："
echo "1. 重新登录: cloudbase login"
echo "2. 确认环境 ID 正确: $ENV_ID"
echo "3. 在 CloudBase 控制台确认环境存在且状态正常"
echo "4. 使用新命令格式: tcb env list"
echo "5. 检查配置文件中的环境 ID 是否正确"
echo ""
