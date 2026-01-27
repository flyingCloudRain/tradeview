"""
龙虎榜API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date as date_type
import math

from app.database.session import get_db
from app.services.lhb_service import LhbService
from app.services.lhb_hot_service import LhbHotService
from app.services.institution_trading_service import InstitutionTradingService
from app.services.active_branch_service import ActiveBranchService
from app.services.active_branch_detail_service import ActiveBranchDetailService
from app.models.lhb import ActiveBranch
from app.schemas.lhb import (
    ActiveBranchDetailStatistics,
    LhbListResponse,
    LhbDetailFullResponse,
    LhbDetailResponse,
    LhbInstitutionResponse,
    LhbHotInstitutionResponse,
    LhbHotListResponse,
    LhbInstitutionItemResponse,
    LhbHotInstitutionDetailResponse,
    InstitutionTradingStatisticsResponse,
    InstitutionTradingStatisticsListResponse,
    InstitutionTradingStatisticsAggregatedResponse,
    ActiveBranchResponse,
    ActiveBranchListResponse,
    ActiveBranchDetailResponse,
    ActiveBranchDetailListResponse,
    BuyStockStatisticsResponse,
    BuyStockStatisticsItem,
    BuyStockBranchesResponse,
    LhbStockStatisticsResponse,
    LhbStockStatisticsItem,
)
from app.utils.date_utils import parse_date
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=LhbListResponse)
def get_lhb_list(
    date: str = Query(..., description="日期，格式：YYYY-MM-DD"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取龙虎榜列表"""
    logger.debug(f"收到请求: date={date}, stock_code={stock_code}, stock_name={stock_name}, page={page}, page_size={page_size}")
    
    target_date = parse_date(date)
    if not target_date:
        logger.warning(f"日期解析失败: {date}")
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    logger.debug(f"解析后的日期: {target_date}")
    
    # 确保order参数有效（处理可能的字符串"undefined"）
    valid_order = order
    if not valid_order or valid_order == "undefined" or valid_order not in ("asc", "desc"):
        valid_order = "desc"
    
    items, total = LhbService.get_lhb_list(
        db=db,
        target_date=target_date,
        stock_code=stock_code,
        stock_name=stock_name,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=valid_order
    )
    
    logger.debug(f"查询结果: {len(items)} 条, total: {total}")
    if len(items) == 0:
        logger.warning(f"查询结果为空，日期: {target_date}")
        # 检查数据库中是否有该日期的数据
        from app.models.lhb import LhbDetail
        db_count = db.query(LhbDetail).filter(LhbDetail.date == target_date).count()
        logger.debug(f"数据库中该日期的数据数量: {db_count}")
    
    # 为每个item添加机构明细信息
    from app.models.lhb import LhbInstitution
    from sqlalchemy import nullslast
    from app.schemas.lhb import LhbDetailResponse, LhbInstitutionResponse
    items_with_institutions = []
    
    try:
        # 批量获取所有机构数据，避免N+1查询问题
        item_ids = [item.id for item in items]
        all_institutions = {}
        if item_ids:
            try:
                # 优化查询：分批查询，避免 IN 子句过长
                # 如果 item_ids 太多，分批处理
                batch_size = 100  # 每批最多100个ID
                institutions_list = []
                
                for i in range(0, len(item_ids), batch_size):
                    batch_ids = item_ids[i:i + batch_size]
                    batch_institutions = db.query(LhbInstitution).filter(
                        LhbInstitution.lhb_detail_id.in_(batch_ids)
                    ).order_by(nullslast(LhbInstitution.net_buy_amount.desc())).all()
                    institutions_list.extend(batch_institutions)
                
                # 按 lhb_detail_id 分组
                for inst in institutions_list:
                    if inst.lhb_detail_id not in all_institutions:
                        all_institutions[inst.lhb_detail_id] = []
                    all_institutions[inst.lhb_detail_id].append(inst)
                    
            except Exception as e:
                logger.error(f"查询机构数据失败: {str(e)}", exc_info=True)
                # 如果查询失败，继续处理但不包含机构信息
        
        for item in items:
            try:
                # 获取该股票的所有机构（已按净买额倒序）
                institutions = all_institutions.get(item.id, [])
                
                # 转换为响应对象
                institution_responses = [
                    LhbInstitutionResponse(
                        id=inst.id,
                        institution_name=inst.institution_name,
                        buy_amount=inst.buy_amount,
                        sell_amount=inst.sell_amount,
                        net_buy_amount=inst.net_buy_amount,
                        flag=inst.flag,
                    )
                    for inst in institutions
                ]
                
                # 创建响应对象（使用 Pydantic 模型）
                item_response = LhbDetailResponse(
                    id=item.id,
                    date=item.date,
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    close_price=item.close_price,
                    change_percent=item.change_percent,
                    net_buy_amount=item.net_buy_amount,
                    buy_amount=item.buy_amount,
                    sell_amount=item.sell_amount,
                    total_amount=item.total_amount,
                    turnover_rate=item.turnover_rate,
                    concept=item.concept,
                    institutions_summary=None,  # 不再使用汇总字符串
                    institutions=institution_responses,  # 返回完整机构列表
                    created_at=item.created_at,
                )
                items_with_institutions.append(item_response)
            except Exception as e:
                logger.error(f"处理股票 {item.stock_code} {item.stock_name} 失败: {str(e)}", exc_info=True)
                # 即使处理失败，也尝试创建基本响应对象
                try:
                    item_response = LhbDetailResponse(
                        id=item.id,
                        date=item.date,
                        stock_code=item.stock_code,
                        stock_name=item.stock_name,
                        close_price=item.close_price,
                        change_percent=item.change_percent,
                        net_buy_amount=item.net_buy_amount,
                        buy_amount=item.buy_amount,
                        sell_amount=item.sell_amount,
                        total_amount=item.total_amount,
                        turnover_rate=item.turnover_rate,
                        concept=item.concept,
                        institutions_summary=None,
                        institutions=[],
                        created_at=item.created_at,
                    )
                    items_with_institutions.append(item_response)
                except:
                    # 如果连基本响应都创建失败，跳过这条记录
                    logger.warning(f"跳过股票 {item.stock_code} {item.stock_name}")
                    continue
    except Exception as e:
        logger.error(f"处理机构信息失败: {str(e)}", exc_info=True)
        # 如果批量处理失败，回退到不包含机构信息的响应
        items_with_institutions = [
            LhbDetailResponse(
                id=item.id,
                date=item.date,
                stock_code=item.stock_code,
                stock_name=item.stock_name,
                close_price=item.close_price,
                change_percent=item.change_percent,
                net_buy_amount=item.net_buy_amount,
                buy_amount=item.buy_amount,
                sell_amount=item.sell_amount,
                total_amount=item.total_amount,
                turnover_rate=item.turnover_rate,
                concept=item.concept,
                institutions_summary=None,
                institutions=[],
                created_at=item.created_at,
            )
            for item in items
        ]
    
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    response = LhbListResponse(
        items=items_with_institutions,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    logger.debug(f"返回响应: items={len(response.items)}, total={response.total}")
    
    return response


@router.get("/stocks-statistics", response_model=LhbStockStatisticsResponse)
def get_lhb_stocks_statistics(
    start_date: str = Query(..., description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式：YYYY-MM-DD"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段：appear_count(上榜次数), total_net_buy_amount(净流入), stock_code, stock_name"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    db: Session = Depends(get_db)
):
    """获取时间跨度内龙虎榜上榜个股统计（统计上榜次数和净流入）"""
    from fastapi import HTTPException
    
    try:
        # 解析日期
        start = parse_date(start_date)
        end = parse_date(end_date)
        
        if not start or not end:
            raise HTTPException(status_code=400, detail="日期格式错误")
        
        if start > end:
            raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
        
        # 确保order参数有效
        valid_order = order
        if not valid_order or valid_order == "undefined" or valid_order not in ("asc", "desc"):
            valid_order = "desc"
        
        # 调用服务方法
        statistics_list, total = LhbService.get_lhb_stocks_statistics(
            db=db,
            start_date=start,
            end_date=end,
            stock_code=stock_code,
            stock_name=stock_name,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=valid_order
        )
        
        # 转换为响应对象
        response_items = [
            LhbStockStatisticsItem(
                stock_code=item['stock_code'],
                stock_name=item['stock_name'],
                appear_count=item['appear_count'],
                total_net_buy_amount=item['total_net_buy_amount'],
                total_buy_amount=item['total_buy_amount'],
                total_sell_amount=item['total_sell_amount'],
                first_date=item['first_date'],
                last_date=item['last_date'],
            )
            for item in statistics_list
        ]
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return LhbStockStatisticsResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            start_date=start,
            end_date=end
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stocks Statistics API 错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"获取上榜个股统计失败: {str(e)}")


@router.get("/institution", response_model=LhbHotListResponse)
def get_lhb_institution(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回最近一次同步的数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段，默认按buy_amount/sell_amount"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    flag: Optional[str] = Query(None, description="操作方向：买入/卖出"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    db: Session = Depends(get_db)
):
    """获取龙虎榜机构榜（直接从 lhb_institution 表查询，包含股票名称）"""

    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        logger.debug(f"Institution API] 收到请求: date={date}, target_date={target_date}, page={page}, page_size={page_size}, flag={flag}, stock_name={stock_name}, stock_code={stock_code}")
        items, total = LhbHotService.get_list(
            db=db,
            target_date=target_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order if order in ("asc", "desc") else "desc",
            flag=flag,
            stock_name=stock_name,
            stock_code=stock_code,
        )
        
        logger.debug(f"Institution API] 查询返回: {len(items)} 条items, total: {total}")
        # 转换为响应对象，包含股票名称
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""

            if value is None:
                return None
            try:
                f = float(value)
                # 检查是否为inf、-inf或NaN
                if math.isinf(f) or math.isnan(f):
                    return None
                return f
            except (ValueError, TypeError, OverflowError):
                return None
        
        response_items = []
        for idx, item in enumerate(items):
            try:
                stock_name = None
                if item.lhb_detail:
                    stock_name = item.lhb_detail.stock_name
                
                # 转换Decimal为float，避免序列化问题
                buy_amount = safe_float(item.buy_amount)
                sell_amount = safe_float(item.sell_amount)
                net_buy_amount = safe_float(item.net_buy_amount)
                
                response_item = LhbInstitutionItemResponse(
                    id=item.id,
                    date=item.date,
                    institution_name=item.institution_name,
                    stock_code=item.stock_code,
                    stock_name=stock_name,
                    flag=item.flag,
                    buy_amount=buy_amount,
                    sell_amount=sell_amount,
                    net_buy_amount=net_buy_amount,
                )
                response_items.append(response_item)
            except Exception as e:
                logger.debug(f"Institution API] 转换第 {idx+1} 条数据失败: {str(e)}")
                logger.debug(f"Institution API] 数据内容: id={item.id}, stock_code={item.stock_code}, institution_name={item.institution_name}")
                logger.debug(f"Institution API] buy_amount类型: {type(item.buy_amount)}, 值: {item.buy_amount}")

                continue
        
        logger.debug(f"Institution API] 返回结果: {len(response_items)} 条, total: {total}")
        if len(response_items) > 0:
            logger.debug(f"Institution API] 第一条数据: {response_items[0].institution_name}, 股票: {response_items[0].stock_name}, 方向: {response_items[0].flag}")
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return LhbHotListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.debug(f"Institution API] 错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"获取机构榜失败: {str(e)}")


@router.get("/institution/{institution_code}/detail", response_model=list[LhbHotInstitutionDetailResponse])
def get_lhb_institution_detail(
    institution_code: str,
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD，可选"),
    db: Session = Depends(get_db)
):
    """获取营业部买入/卖出股票明细（即时调用 ak.stock_lhb_yyb_detail_em，不落库）"""
    target_date = parse_date(date) if date else None
    records = LhbHotService.get_institution_detail(
        institution_code=institution_code,
        target_date=target_date,
    )
    return records


@router.get("/institution-trading-statistics", response_model=InstitutionTradingStatisticsListResponse)
def get_institution_trading_statistics(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回最近一次同步的数据（与start_date/end_date互斥）"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD（时间段查询）"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD（时间段查询）"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段，默认按institution_net_buy_amount"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    db: Session = Depends(get_db)
):
    """获取机构交易统计数据"""

    from fastapi import HTTPException
    
    try:
        # 解析日期参数
        target_date = parse_date(date) if date else None
        start_date_parsed = parse_date(start_date) if start_date else None
        end_date_parsed = parse_date(end_date) if end_date else None
        
        # 验证日期参数：date 和 start_date/end_date 不能同时使用
        if target_date and (start_date_parsed or end_date_parsed):
            raise HTTPException(status_code=400, detail="date 参数与 start_date/end_date 参数不能同时使用")
        
        # 验证时间段参数
        if start_date_parsed and end_date_parsed and start_date_parsed > end_date_parsed:
            raise HTTPException(status_code=400, detail="start_date 不能大于 end_date")
        
        logger.debug(f"收到请求: date={date}, target_date={target_date}, start_date={start_date}, end_date={end_date}, page={page}, page_size={page_size}, stock_code={stock_code}, stock_name={stock_name}")
        items, total = InstitutionTradingService.get_list(
            db=db,
            target_date=target_date,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            stock_code=stock_code,
            stock_name=stock_name,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order if order in ("asc", "desc") else "desc",
        )
        
        logger.debug(f"查询返回: {len(items)} 条items, total: {total}")
        # 转换为响应对象
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""

            if value is None:
                return None
            try:
                f = float(value)
                # 检查是否为inf、-inf或NaN
                if math.isinf(f) or math.isnan(f):
                    return None
                return f
            except (ValueError, TypeError, OverflowError):
                return None
        
        response_items = []
        for idx, item in enumerate(items):
            try:
                response_item = InstitutionTradingStatisticsResponse(
                    id=item.id,
                    date=item.date,
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    close_price=safe_float(item.close_price),
                    change_percent=safe_float(item.change_percent),
                    institution_net_buy_amount=safe_float(item.institution_net_buy_amount),  # 机构买入净额
                    buyer_institution_count=item.buyer_institution_count,
                    seller_institution_count=item.seller_institution_count,
                    institution_buy_amount=safe_float(item.institution_buy_amount),
                    institution_sell_amount=safe_float(item.institution_sell_amount),
                    market_total_amount=safe_float(item.market_total_amount),
                    net_buy_ratio=safe_float(item.net_buy_ratio),
                    turnover_rate=safe_float(item.turnover_rate),
                    circulation_market_value=safe_float(item.circulation_market_value),
                    created_at=item.created_at,
                )
                response_items.append(response_item)
            except Exception as e:
                logger.debug(f"转换第 {idx+1} 条数据失败: {str(e)}")

                continue
        
        logger.debug(f"返回结果: {len(response_items)} 条, total: {total}")
        if len(response_items) > 0:
            logger.debug(f"第一条数据: {response_items[0].stock_name} ({response_items[0].stock_code})")
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return InstitutionTradingStatisticsListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.debug(f"错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"获取机构交易统计数据失败: {str(e)}")


@router.get("/institution-trading-statistics/aggregated", response_model=InstitutionTradingStatisticsAggregatedResponse)
def get_institution_trading_statistics_aggregated(
    start_date: str = Query(..., description="开始日期，格式：YYYY-MM-DD"),
    end_date: str = Query(..., description="结束日期，格式：YYYY-MM-DD"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    min_appear_count: Optional[int] = Query(None, ge=0, description="最小上榜次数"),
    max_appear_count: Optional[int] = Query(None, ge=0, description="最大上榜次数"),
    min_total_net_buy_amount: Optional[float] = Query(None, description="最小累计净买入金额"),
    max_total_net_buy_amount: Optional[float] = Query(None, description="最大累计净买入金额"),
    min_total_buy_amount: Optional[float] = Query(None, description="最小累计买入金额"),
    max_total_buy_amount: Optional[float] = Query(None, description="最大累计买入金额"),
    min_total_sell_amount: Optional[float] = Query(None, description="最小累计卖出金额"),
    max_total_sell_amount: Optional[float] = Query(None, description="最大累计卖出金额"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段，支持：institution_net_buy_amount, institution_buy_amount, institution_sell_amount, appear_count, total_market_amount, net_buy_ratio"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    db: Session = Depends(get_db)
):
    """获取时间段内的机构交易统计汇总（按股票代码聚合）"""

    from fastapi import HTTPException
    
    try:
        # 解析日期参数
        start_date_parsed = parse_date(start_date)
        end_date_parsed = parse_date(end_date)
        
        if not start_date_parsed or not end_date_parsed:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD 格式")
        
        if start_date_parsed > end_date_parsed:
            raise HTTPException(status_code=400, detail="start_date 不能大于 end_date")
        
        logger.debug(f"收到请求: start_date={start_date}, end_date={end_date}, page={page}, page_size={page_size}, stock_code={stock_code}, stock_name={stock_name}, min_appear_count={min_appear_count}, min_total_net_buy_amount={min_total_net_buy_amount}")
        items, total = InstitutionTradingService.get_aggregated_statistics(
            db=db,
            start_date=start_date_parsed,
            end_date=end_date_parsed,
            stock_code=stock_code,
            stock_name=stock_name,
            min_appear_count=min_appear_count,
            max_appear_count=max_appear_count,
            min_total_net_buy_amount=min_total_net_buy_amount,
            max_total_net_buy_amount=max_total_net_buy_amount,
            min_total_buy_amount=min_total_buy_amount,
            max_total_buy_amount=max_total_buy_amount,
            min_total_sell_amount=min_total_sell_amount,
            max_total_sell_amount=max_total_sell_amount,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order if order in ("asc", "desc") else "desc",
        )
        
        logger.debug(f"查询返回: {len(items)} 条items, total: {total}")
        # 转换为响应对象
        from app.schemas.lhb import InstitutionTradingStatisticsAggregatedItem
        
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""

            if value is None:
                return None
            try:
                f = float(value)
                # 检查是否为inf、-inf或NaN
                if math.isinf(f) or math.isnan(f):
                    return None
                return f
            except (ValueError, TypeError):
                return None
        
        response_items = []
        for item in items:
            try:
                response_item = InstitutionTradingStatisticsAggregatedItem(
                    stock_code=item['stock_code'],
                    stock_name=item['stock_name'],
                    appear_count=item['appear_count'],
                    total_buy_amount=safe_float(item.get('total_buy_amount')),
                    total_sell_amount=safe_float(item.get('total_sell_amount')),
                    total_net_buy_amount=safe_float(item.get('total_net_buy_amount')),
                    total_market_amount=safe_float(item.get('total_market_amount')),
                    net_buy_ratio=safe_float(item.get('net_buy_ratio')),
                    avg_close_price=safe_float(item.get('avg_close_price')),
                    avg_circulation_market_value=safe_float(item.get('avg_circulation_market_value')),
                    avg_turnover_rate=safe_float(item.get('avg_turnover_rate')),
                    max_change_percent=safe_float(item.get('max_change_percent')),
                    min_change_percent=safe_float(item.get('min_change_percent')),
                    earliest_date=item['earliest_date'],
                    latest_date=item['latest_date'],
                )
                response_items.append(response_item)
            except Exception as e:
                logger.error(f"转换数据项失败: {str(e)}, item: {item}", exc_info=True)
                # 跳过有问题的数据项，继续处理其他项
                continue
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return InstitutionTradingStatisticsAggregatedResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取机构交易统计汇总失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取机构交易统计汇总失败: {str(e)}")


@router.get("/active-branch", response_model=ActiveBranchListResponse)
def get_active_branch_list(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回最近一次同步的数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段，默认按net_amount"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    institution_name: Optional[str] = Query(None, description="营业部名称（模糊查询）"),
    institution_code: Optional[str] = Query(None, description="营业部代码"),
    buy_stock_name: Optional[str] = Query(None, description="买入股票名称（查询买入该股票的营业部）"),
    db: Session = Depends(get_db)
):
    """获取活跃营业部列表"""

    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        logger.debug(f"收到请求: date={date}, target_date={target_date}, page={page}, page_size={page_size}, sort_by={sort_by}, order={order}, institution_name={institution_name}, institution_code={institution_code}, buy_stock_name={buy_stock_name}")
        items, total = ActiveBranchService.get_list(
            db=db,
            target_date=target_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order if order in ("asc", "desc") else "desc",
            institution_name=institution_name,
            institution_code=institution_code,
            buy_stock_name=buy_stock_name,
        )
        
        logger.debug(f"查询返回: {len(items)} 条items, total: {total}")
        # 转换为响应对象
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""

            if value is None:
                return None
            try:
                f = float(value)
                if math.isinf(f) or math.isnan(f):
                    return None
                return f
            except (ValueError, TypeError, OverflowError):
                return None
        
        response_items = []
        for idx, item in enumerate(items):
            try:
                response_item = ActiveBranchResponse(
                    id=item.id,
                    date=item.date,
                    institution_name=item.institution_name,
                    institution_code=item.institution_code,
                    buy_stock_count=item.buy_stock_count,
                    sell_stock_count=item.sell_stock_count,
                    buy_amount=safe_float(item.buy_amount),
                    sell_amount=safe_float(item.sell_amount),
                    net_amount=safe_float(item.net_amount),
                    buy_stocks=item.buy_stocks,
                    created_at=item.created_at,
                )
                response_items.append(response_item)
            except Exception as e:
                logger.debug(f"转换第 {idx+1} 条数据失败: {str(e)}")

                continue
        
        logger.debug(f"返回结果: {len(response_items)} 条, total: {total}")
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ActiveBranchListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.debug(f"错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"获取活跃营业部列表失败: {str(e)}")


@router.get("/active-branch/{institution_code}/detail", response_model=ActiveBranchDetailListResponse)
def get_active_branch_detail(
    institution_code: str,
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回所有日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段，默认按date"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    stock_name: Optional[str] = Query(None, description="股票名称（模糊查询）"),
    db: Session = Depends(get_db)
):
    """获取活跃营业部交易详情"""

    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        
        items, total = ActiveBranchDetailService.get_list(
            db=db,
            institution_code=institution_code,
            target_date=target_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order if order in ("asc", "desc") else "desc",
            stock_code=stock_code,
            stock_name=stock_name,
        )
        
        # 转换为响应对象
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""

            if value is None:
                return None
            try:
                f = float(value)
                if math.isinf(f) or math.isnan(f):
                    return None
                return f
            except (ValueError, TypeError, OverflowError):
                return None
        
        response_items = []
        for item in items:
            try:
                response_item = ActiveBranchDetailResponse(
                    id=item.id,
                    institution_code=item.institution_code,
                    institution_name=item.institution_name,
                    date=item.date,
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    change_percent=safe_float(item.change_percent),
                    buy_amount=safe_float(item.buy_amount),
                    sell_amount=safe_float(item.sell_amount),
                    net_amount=safe_float(item.net_amount),
                    reason=item.reason,
                    after_1d=safe_float(item.after_1d),
                    after_2d=safe_float(item.after_2d),
                    after_3d=safe_float(item.after_3d),
                    after_5d=safe_float(item.after_5d),
                    after_10d=safe_float(item.after_10d),
                    after_20d=safe_float(item.after_20d),
                    after_30d=safe_float(item.after_30d),
                    created_at=item.created_at,
                )
                response_items.append(response_item)
            except Exception as e:
                logger.debug(f"转换数据失败: {str(e)}")
                continue
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ActiveBranchDetailListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        logger.debug(f"错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"获取活跃营业部交易详情失败: {str(e)}")


@router.get("/active-branch/buy-stocks-statistics", response_model=BuyStockStatisticsResponse)
def get_buy_stocks_statistics(
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回最近一次同步的数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取活跃营业部买入股票统计（按出现次数排序）"""

    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        logger.debug(f"收到请求: date={date}, target_date={target_date}, page={page}, page_size={page_size}")
        statistics, total = ActiveBranchService.get_buy_stocks_statistics(
            db=db,
            target_date=target_date,
            page=page,
            page_size=page_size,
        )
        
        # 如果没有指定日期，需要获取实际使用的日期
        if not target_date:
            from sqlalchemy import func
            target_date = db.query(func.max(ActiveBranch.date)).scalar()
        
        logger.debug(f"查询返回: {len(statistics)} 条items, total: {total}")
        # 转换为响应对象
        response_items = [
            BuyStockStatisticsItem(
                stock_name=item["stock_name"],
                appear_count=item["appear_count"],
                buy_branch_count=item.get("buy_branch_count", 0),
                sell_branch_count=item.get("sell_branch_count", 0),
                net_buy_amount=item.get("net_buy_amount", 0.0),
                net_sell_amount=item.get("net_sell_amount", 0.0),
            )
            for item in statistics
        ]
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return BuyStockStatisticsResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            date=target_date if target_date else date_type.today()
        )
    except Exception as e:
        logger.debug(f"错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"获取买入股票统计失败: {str(e)}")


@router.get("/active-branch/buy-stocks-statistics/{stock_name}/branches", response_model=BuyStockBranchesResponse)
def get_branches_by_stock_name(
    stock_name: str,
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回最近一次同步的数据"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    db: Session = Depends(get_db)
):
    """根据股票名称查询买入该股票的所有营业部记录"""

    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        logger.debug(f"收到请求: stock_name={stock_name}, date={date}, target_date={target_date}, page={page}, page_size={page_size}")
        records, total = ActiveBranchService.get_branches_by_stock_name(
            db=db,
            stock_name=stock_name,
            target_date=target_date,
            page=page,
            page_size=page_size,
        )
        
        # 如果没有指定日期，需要获取实际使用的日期
        if not target_date:
            from sqlalchemy import func
            target_date = db.query(func.max(ActiveBranch.date)).scalar()
        
        logger.debug(f"查询返回: {len(records)} 条items, total: {total}")
        # 转换为响应对象
        response_items = [
            ActiveBranchResponse(
                id=record.id,
                date=record.date,
                institution_name=record.institution_name,
                institution_code=record.institution_code,
                buy_stock_count=record.buy_stock_count,
                sell_stock_count=record.sell_stock_count,
                buy_amount=record.buy_amount,
                sell_amount=record.sell_amount,
                net_amount=record.net_amount,
                buy_stocks=record.buy_stocks,
                created_at=record.created_at if hasattr(record, 'created_at') else None,
            )
            for record in records
        ]
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return BuyStockBranchesResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            stock_name=stock_name,
            date=target_date if target_date else date_type.today()
        )
    except Exception as e:
        logger.debug(f"错误: {str(e)}")

        raise HTTPException(status_code=500, detail=f"查询买入股票 {stock_name} 的营业部记录失败: {str(e)}")


@router.get("/active-branch-detail/by-stock-name", response_model=ActiveBranchDetailListResponse)
def get_active_branch_detail_by_stock_name(
    stock_name: str = Query(..., description="股票名称（精确匹配）"),
    date: Optional[str] = Query(None, description="日期，格式：YYYY-MM-DD；为空时返回所有日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段，默认按date"),
    order: str = Query("desc", description="排序方向 asc/desc"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    db: Session = Depends(get_db)
):
    """根据股票名称获取活跃营业部交易详情"""

    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        
        items, total = ActiveBranchDetailService.get_list(
            db=db,
            institution_code=None,  # 不限制营业部
            target_date=target_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order if order in ("asc", "desc") else "desc",
            stock_code=stock_code,
            stock_name=stock_name,
        )
        
        # 转换为响应对象
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""

            if value is None:
                return None
            try:
                f = float(value)
                if math.isinf(f) or math.isnan(f):
                    return None
                return f
            except (ValueError, TypeError, OverflowError):
                return None
        
        response_items = []
        for item in items:
            try:
                response_item = ActiveBranchDetailResponse(
                    id=item.id,
                    institution_code=item.institution_code,
                    institution_name=item.institution_name,
                    date=item.date,
                    stock_code=item.stock_code,
                    stock_name=item.stock_name,
                    change_percent=safe_float(item.change_percent),
                    buy_amount=safe_float(item.buy_amount),
                    sell_amount=safe_float(item.sell_amount),
                    net_amount=safe_float(item.net_amount),
                    reason=item.reason,
                    after_1d=safe_float(item.after_1d),
                    after_2d=safe_float(item.after_2d),
                    after_3d=safe_float(item.after_3d),
                    after_5d=safe_float(item.after_5d),
                    after_10d=safe_float(item.after_10d),
                    after_20d=safe_float(item.after_20d),
                    after_30d=safe_float(item.after_30d),
                    created_at=item.created_at,
                )
                response_items.append(response_item)
            except Exception as e:
                logger.error(f"转换数据失败: {str(e)}", exc_info=True)
                continue
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        # 获取统计信息
        statistics = ActiveBranchDetailService.get_statistics(
            db=db,
            institution_code=None,
            target_date=target_date,
            stock_code=stock_code,
            stock_name=stock_name,
        )
        
        return ActiveBranchDetailListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            statistics=ActiveBranchDetailStatistics(**statistics)
        )
    except Exception as e:
        logger.error(f"获取活跃营业部交易详情失败: {str(e)}", exc_info=True)

        raise HTTPException(status_code=500, detail=f"获取股票活跃营业部交易详情失败: {str(e)}")


@router.get("/{stock_code}", response_model=LhbDetailFullResponse)
def get_lhb_detail(
    stock_code: str,
    date: str = Query(..., description="日期"),
    db: Session = Depends(get_db)
):
    """获取龙虎榜详情"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    detail = LhbService.get_lhb_detail(db, stock_code, target_date)
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="未找到数据")
    
    institutions = LhbService.get_institution_detail(db, stock_code, target_date)
    
    return LhbDetailFullResponse(
        detail=detail,
        institutions=institutions
    )


@router.get("/{stock_code}/institution", response_model=list[LhbInstitutionResponse])
def get_institution_detail(
    stock_code: str,
    date: str = Query(..., description="日期"),
    db: Session = Depends(get_db)
):
    """获取机构明细"""
    target_date = parse_date(date)
    if not target_date:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    institutions = LhbService.get_institution_detail(db, stock_code, target_date)
    return institutions

