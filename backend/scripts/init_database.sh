#!/bin/bash

# 数据库初始化脚本

echo "=========================================="
echo "交易复盘系统 - 数据库初始化"
echo "=========================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "app/main.py" ]; then
    echo "❌ 错误: 请在backend目录下运行此脚本"
    exit 1
fi

echo ""
echo "选择初始化方式:"
echo "1. 使用Python脚本创建表（推荐）"
echo "2. 使用Alembic迁移"
echo "3. 使用SQL脚本"
read -p "请选择 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "使用Python脚本创建表..."
        python3 scripts/init_database.py
        ;;
    2)
        echo ""
        echo "使用Alembic迁移..."
        if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
            echo "创建初始迁移..."
            alembic revision --autogenerate -m "Initial migration"
        fi
        echo "执行迁移..."
        alembic upgrade head
        ;;
    3)
        echo ""
        echo "使用SQL脚本..."
        if [ -z "$DATABASE_URL" ]; then
            read -p "请输入数据库连接字符串: " db_url
            export DATABASE_URL="$db_url"
        fi
        psql $DATABASE_URL -f scripts/create_tables.sql
        ;;
    *)
        echo "❌ 无效的选择"
        exit 1
        ;;
esac

echo ""
echo "✅ 数据库初始化完成！"

