"""
API v1路由
"""
from fastapi import APIRouter
from app.api.v1 import lhb, zt_pool, zt_pool_down, index, sector, fund_flow as stock_fund_flow, capital, trading_calendar, task, stock_concept, limit_up_board

api_router = APIRouter()

api_router.include_router(lhb.router, prefix="/lhb", tags=["龙虎榜"])
api_router.include_router(zt_pool.router, prefix="/zt-pool", tags=["涨停池"])
api_router.include_router(zt_pool_down.router, prefix="/zt-pool-down", tags=["跌停池"])
api_router.include_router(index.router, prefix="/index", tags=["大盘指数"])
api_router.include_router(sector.router, prefix="/sector", tags=["概念板块"])
api_router.include_router(stock_fund_flow.router, prefix="/stock-fund-flow", tags=["个股资金流"])
api_router.include_router(capital.router, prefix="/capital", tags=["活跃机构"])
api_router.include_router(trading_calendar.router, prefix="/trading-calendar", tags=["交易日历"])
api_router.include_router(task.router, prefix="/tasks", tags=["任务管理"])
api_router.include_router(stock_concept.router, prefix="/stock-concepts", tags=["股票概念板块"])
api_router.include_router(limit_up_board.router, prefix="/limit-up-board", tags=["涨停板分析"])

