#!/bin/bash

# 检查后端服务健康状态

set -e

BACKEND_URL="https://trading-api-wwbrnphpuq-uc.a.run.app"
FRONTEND_URL="https://trading-frontend-541241838218.us-central1.run.app"

echo "=========================================="
echo "检查后端服务健康状态"
echo "=========================================="
echo ""

echo "1. 检查健康检查端点..."
echo "   URL: $BACKEND_URL/health"
echo ""

HEALTH_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL/health" || echo "ERROR")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
BODY=$(echo "$HEALTH_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ 健康检查通过 (HTTP $HTTP_CODE)"
    echo "   响应: $BODY"
elif [ "$HTTP_CODE" = "500" ]; then
    echo "   ❌ 健康检查失败 (HTTP $HTTP_CODE)"
    echo "   响应: $BODY"
    echo ""
    echo "   可能的原因："
    echo "   - 应用启动错误"
    echo "   - 数据库连接问题"
    echo "   - 路由注册失败"
    echo ""
    echo "   查看日志："
    echo "   gcloud functions logs read trading-api --gen2 --region=us-central1 --limit=50"
elif [ -z "$HTTP_CODE" ] || [ "$HTTP_CODE" = "ERROR" ]; then
    echo "   ❌ 无法连接到后端服务"
    echo ""
    echo "   可能的原因："
    echo "   - 服务未部署"
    echo "   - 网络连接问题"
    echo "   - DNS 解析问题"
else
    echo "   ⚠️  意外状态码: HTTP $HTTP_CODE"
    echo "   响应: $BODY"
fi

echo ""
echo "2. 检查根路径..."
echo "   URL: $BACKEND_URL/"
echo ""

ROOT_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BACKEND_URL/" || echo "ERROR")
ROOT_HTTP_CODE=$(echo "$ROOT_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
ROOT_BODY=$(echo "$ROOT_RESPONSE" | sed '/HTTP_CODE/d')

if [ "$ROOT_HTTP_CODE" = "200" ]; then
    echo "   ✅ 根路径可访问 (HTTP $ROOT_HTTP_CODE)"
    echo "   响应: $ROOT_BODY"
else
    echo "   ⚠️  根路径状态码: HTTP $ROOT_HTTP_CODE"
    echo "   响应: $ROOT_BODY"
fi

echo ""
echo "3. 检查 CORS 预检请求..."
echo "   URL: $BACKEND_URL/api/v1/zt-pool/"
echo "   Origin: $FRONTEND_URL"
echo ""

CORS_RESPONSE=$(curl -s -X OPTIONS \
    -H "Origin: $FRONTEND_URL" \
    -H "Access-Control-Request-Method: GET" \
    -H "Access-Control-Request-Headers: Content-Type" \
    -w "\nHTTP_CODE:%{http_code}" \
    "$BACKEND_URL/api/v1/zt-pool/" || echo "ERROR")

CORS_HTTP_CODE=$(echo "$CORS_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
CORS_HEADERS=$(echo "$CORS_RESPONSE" | sed '/HTTP_CODE/d' | head -20)

if [ "$CORS_HTTP_CODE" = "200" ] || [ "$CORS_HTTP_CODE" = "204" ]; then
    echo "   ✅ CORS 预检请求成功 (HTTP $CORS_HTTP_CODE)"
    if echo "$CORS_HEADERS" | grep -q "Access-Control-Allow-Origin"; then
        echo "   ✅ CORS 头已设置"
    else
        echo "   ⚠️  CORS 头未找到"
    fi
else
    echo "   ⚠️  CORS 预检请求状态码: HTTP $CORS_HTTP_CODE"
fi

echo ""
echo "4. 检查 API 端点..."
echo "   URL: $BACKEND_URL/api/v1/zt-pool/?start_date=2026-01-27&end_date=2026-01-27&page=1&page_size=1"
echo ""

API_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
    -H "Origin: $FRONTEND_URL" \
    "$BACKEND_URL/api/v1/zt-pool/?start_date=2026-01-27&end_date=2026-01-27&page=1&page_size=1" || echo "ERROR")

API_HTTP_CODE=$(echo "$API_RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
API_BODY=$(echo "$API_RESPONSE" | sed '/HTTP_CODE/d' | head -5)

if [ "$API_HTTP_CODE" = "200" ]; then
    echo "   ✅ API 端点可访问 (HTTP $API_HTTP_CODE)"
    echo "   响应预览: $(echo "$API_BODY" | head -1)"
elif [ "$API_HTTP_CODE" = "500" ]; then
    echo "   ❌ API 端点返回 500 错误"
    echo "   响应: $API_BODY"
elif [ -z "$API_HTTP_CODE" ] || [ "$API_HTTP_CODE" = "ERROR" ]; then
    echo "   ❌ 无法连接到 API 端点"
else
    echo "   ⚠️  API 端点状态码: HTTP $API_HTTP_CODE"
    echo "   响应: $API_BODY"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "如果后端服务有问题，查看日志："
echo "  gcloud functions logs read trading-api --gen2 --region=us-central1 --limit=50 --filter='severity>=ERROR'"
echo ""
