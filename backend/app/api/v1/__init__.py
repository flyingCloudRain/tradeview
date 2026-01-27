"""
API v1路由
"""
from fastapi import APIRouter

api_router = APIRouter()

# 安全导入和注册路由，即使某个路由导入失败也能继续
def safe_include_router(module_name, router_attr, prefix, tags):
    """安全地导入和注册路由"""
    try:
        module = __import__(f"app.api.v1.{module_name}", fromlist=[router_attr])
        router = getattr(module, router_attr)
        api_router.include_router(router, prefix=prefix, tags=tags)
        print(f"✅ 成功注册路由: {prefix}")
    except Exception as e:
        print(f"⚠️  路由注册失败 {prefix}: {e}")
        import traceback
        traceback.print_exc()

# 注册所有路由
safe_include_router("lhb", "router", "/lhb", ["龙虎榜"])
safe_include_router("zt_pool", "router", "/zt-pool", ["涨停池"])
safe_include_router("zt_pool_down", "router", "/zt-pool-down", ["跌停池"])
safe_include_router("index", "router", "/index", ["大盘指数"])
safe_include_router("sector", "router", "/sector", ["概念板块"])
safe_include_router("fund_flow", "router", "/stock-fund-flow", ["个股资金流"])
safe_include_router("capital", "router", "/capital", ["活跃机构"])
safe_include_router("trading_calendar", "router", "/trading-calendar", ["交易日历"])
safe_include_router("task", "router", "/tasks", ["任务管理"])
safe_include_router("stock_concept", "router", "/stock-concepts", ["股票概念板块"])
safe_include_router("limit_up_board", "router", "/limit-up-board", ["涨停板分析"])

