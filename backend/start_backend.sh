#!/bin/bash
# 启动后端服务脚本

cd "$(dirname "$0")"

# 检查数据库URL是否设置（必须使用Supabase PostgreSQL）
if [ -z "$DATABASE_URL" ]; then
    echo "❌ 错误: DATABASE_URL 环境变量未设置"
    echo ""
    echo "请设置 DATABASE_URL 环境变量指向 Supabase 数据库:"
    echo "  export DATABASE_URL=\"postgresql://postgres:password@db.xxx.supabase.co:5432/postgres\""
    echo ""
    echo "或者使用 setup_env.sh 脚本:"
    echo "  source backend/setup_env.sh"
    exit 1
fi

# 验证数据库URL是否为PostgreSQL/Supabase
if [[ ! "$DATABASE_URL" =~ ^postgresql:// ]]; then
    echo "⚠️  警告: DATABASE_URL 不是 PostgreSQL 连接字符串"
    echo "   当前值: $DATABASE_URL"
    echo "   请确保使用 Supabase PostgreSQL 数据库"
fi

echo "启动后端服务..."
echo "DATABASE_URL: ${DATABASE_URL%%@*}@***"  # 隐藏密码部分
echo ""

uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
