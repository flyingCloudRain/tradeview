#!/bin/bash
# 设置环境变量脚本

# 数据库连接字符串
export DATABASE_URL="postgresql://postgres:aqLt2k477NarCPpf@db.uvtmbjgndhcmlupridss.supabase.co:5432/postgres"

# Supabase配置
export SUPABASE_URL="https://uvtmbjgndhcmlupridss.supabase.co"

# 日志配置
export LOG_LEVEL="INFO"

echo "环境变量已设置:"
echo "DATABASE_URL=$DATABASE_URL"
echo "SUPABASE_URL=$SUPABASE_URL"

