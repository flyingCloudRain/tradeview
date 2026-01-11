#!/bin/bash
# 检查Supabase数据库中trader_branch表的数据
# 使用方法: 
#   1. 设置DATABASE_URL环境变量: export DATABASE_URL="postgresql://user:password@host:port/database"
#   2. 运行: bash backend/scripts/check_supabase.sh

echo "=========================================="
echo "检查 Supabase trader_branch 表数据"
echo "=========================================="
echo ""

# 检查DATABASE_URL是否设置
if [ -z "$DATABASE_URL" ]; then
    echo "❌ 错误: DATABASE_URL 环境变量未设置"
    echo ""
    echo "请设置 DATABASE_URL 环境变量指向 Supabase 数据库:"
    echo "  export DATABASE_URL=\"postgresql://user:password@host:port/database\""
    echo ""
    echo "或者从 .env 文件加载:"
    echo "  source backend/setup_env.sh"
    echo ""
    exit 1
fi

echo "✅ DATABASE_URL 已设置"
echo "   数据库类型: $(echo $DATABASE_URL | grep -o '^[^:]*')"
echo ""

# 运行Python检查脚本
PYTHONPATH=. python backend/scripts/check_supabase_trader_branch.py
