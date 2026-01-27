"""
资金流API路由
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.database.session import get_db
from app.services.fund_flow_service import FundFlowService
from app.utils.date_utils import parse_date, get_trading_date, get_trading_dates_before
from app.config import settings
from app.schemas.fund_flow import FundFlowFilterRequest, ConceptFundFlowFilterRequest

router = APIRouter()


@router.get("/")
def get_fund_flow_list(
    date: Optional[str] = Query(None, description="日期（单日期查询，可选，与日期范围查询互斥）"),
    start_date: Optional[str] = Query(None, description="开始日期（日期范围查询，可选，默认最近3日）"),
    end_date: Optional[str] = Query(None, description="结束日期（日期范围查询，可选，默认最近3日）"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept_ids: Optional[str] = Query(None, description="概念板块ID列表（逗号分隔，如：1,2,3）"),
    concept_names: Optional[str] = Query(None, description="概念板块名称列表（逗号分隔，如：人工智能,新能源）"),
    consecutive_days: Optional[int] = Query(None, ge=1, description="连续N日，净流入>M的查询条件（N）"),
    min_net_inflow: Optional[float] = Query(None, ge=0, description="连续N日，净流入>M的查询条件（M，单位：元，如100000000表示1亿）"),
    is_limit_up: Optional[bool] = Query(None, description="是否涨停，True=仅涨停，False=仅非涨停，None=全部"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量，默认50"),
    sort_by: Optional[str] = Query("main_net_inflow", description="排序字段，如 main_net_inflow/main_inflow/main_outflow/turnover_rate/change_percent"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """
    获取资金流列表
    
    支持两种查询模式：
    1. 单日期查询：使用 date 参数
    2. 日期范围查询：使用 start_date 和 end_date 参数
    
    如果都没有提供，默认查询最近3个交易日的数据
    """
    from app.utils.date_utils import get_trading_dates_before
    
    # 确定查询日期范围
    if start_date and end_date:
        # 日期范围查询
        start = parse_date(start_date)
        end = parse_date(end_date)
        if not start or not end:
            raise HTTPException(status_code=400, detail="日期格式错误")
        if start > end:
            raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
        target_date = None  # 使用日期范围
    elif date:
        # 单日期查询（保持向后兼容）
        target_date = parse_date(date)
        if not target_date:
            raise HTTPException(status_code=400, detail="日期格式错误")
        start = None
        end = None
    else:
        # 默认查询最近3个交易日
        latest_date = get_trading_date()
        if not latest_date:
            raise HTTPException(status_code=404, detail="未找到可用的交易日期")
        # 获取最近3个交易日
        trading_dates = get_trading_dates_before(db, latest_date, 3)
        if not trading_dates:
            raise HTTPException(status_code=404, detail="未找到可用的交易日期")
        start = min(trading_dates)
        end = max(trading_dates)
        target_date = None  # 使用日期范围
    
    # 解析概念板块参数
    concept_ids_list = None
    if concept_ids:
        try:
            concept_ids_list = [int(x.strip()) for x in concept_ids.split(',') if x.strip()]
        except ValueError:
            raise HTTPException(status_code=400, detail="概念板块ID格式错误")
    
    concept_names_list = None
    if concept_names:
        concept_names_list = [x.strip() for x in concept_names.split(',') if x.strip()]
    
    # 根据查询模式调用不同的服务方法
    if target_date is not None:
        # 单日期查询
        items, total = FundFlowService.get_fund_flow_list(
            db=db,
            target_date=target_date,
            stock_code=stock_code,
            concept_ids=concept_ids_list,
            concept_names=concept_names_list,
            consecutive_days=consecutive_days,
            min_net_inflow=min_net_inflow,
            is_limit_up=is_limit_up,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
        )
    else:
        # 日期范围查询
        items, total = FundFlowService.get_fund_flow_list_by_date_range(
            db=db,
            start_date=start,
            end_date=end,
            stock_code=stock_code,
            concept_ids=concept_ids_list,
            concept_names=concept_names_list,
            consecutive_days=consecutive_days,
            min_net_inflow=min_net_inflow,
            is_limit_up=is_limit_up,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            order=order,
        )
    
    # 将items转换为字典，添加concepts字段
    items_dict = []
    for item in items:
        item_dict = {
            column.name: getattr(item, column.name)
            for column in item.__table__.columns
        }
        # 添加概念板块
        if hasattr(item, '_concepts'):
            item_dict['concepts'] = [
                {"id": c.id, "name": c.name, "code": c.code}
                for c in item._concepts
            ]
        else:
            item_dict['concepts'] = []
        items_dict.append(item_dict)
    
    return {
        "items": items_dict,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size)
    }


@router.get("/{stock_code}/history")
def get_fund_flow_history(
    stock_code: str,
    start_date: str = Query(..., description="开始日期"),
    end_date: str = Query(..., description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取资金流历史"""
    start = parse_date(start_date)
    end = parse_date(end_date)
    if not start or not end:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    items = FundFlowService.get_fund_flow_history(db, stock_code, start, end)
    return items


@router.get("/concept")
def get_concept_fund_flow(
    date: Optional[str] = Query(None, description="日期，格式YYYY-MM-DD（单日期查询，可选）"),
    start_date: Optional[str] = Query(None, description="开始日期，格式YYYY-MM-DD（日期范围查询）"),
    end_date: Optional[str] = Query(None, description="结束日期，格式YYYY-MM-DD（日期范围查询）"),
    concept: Optional[str] = Query(None, description="概念名称（模糊匹配）"),
    limit: int = Query(50, ge=1, le=200, description="返回条数，默认50，最大200（仅单日期查询时有效）"),
    page: int = Query(1, ge=1, description="页码（日期范围查询时有效）"),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量（日期范围查询时有效）"),
    sort_by: Optional[str] = Query("net_amount", description="排序字段（日期范围查询时有效）"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向（日期范围查询时有效）"),
    db: Session = Depends(get_db),
):
    """
    获取概念资金流
    
    支持两种查询模式：
    1. 单日期查询：使用 date 参数，返回指定日期的概念资金流数据
    2. 日期范围查询：使用 start_date 和 end_date 参数，返回日期范围内的概念资金流数据
    
    如果 date 和日期范围都为空，则查询最新日期的数据
    """
    # 日期范围查询优先级高于单日期查询
    if start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)
        if not start or not end:
            raise HTTPException(status_code=400, detail="日期格式错误")
        if start > end:
            raise HTTPException(status_code=400, detail="开始日期不能大于结束日期")
        
        # 使用日期范围查询
        concepts_list = [concept] if concept else None
        items, total = FundFlowService.get_concept_fund_flow_by_date_range(
            db=db,
            start_date=start,
            end_date=end,
            concepts=concepts_list,
            sort_by=sort_by,
            order=order,
            page=page,
            page_size=page_size
        )
        
        # 转换为字典列表
        items_dict = []
        for item in items:
            item_dict = {
                column.name: getattr(item, column.name)
                for column in item.__table__.columns
            }
            items_dict.append(item_dict)
        
        return {
            "items": items_dict,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size > 0 else 0
        }
    else:
        # 单日期查询
        if date:
            target_date = parse_date(date)
            if not target_date:
                raise HTTPException(status_code=400, detail="日期格式错误")
        else:
            # 如果日期为空，查询最新日期
            target_date = get_trading_date()
            if not target_date:
                raise HTTPException(status_code=404, detail="未找到可用的交易日期")
        
        items = FundFlowService.get_concept_fund_flow_db(db, target_date, limit=limit)
        
        # 如果指定日期没有数据，尝试查询最近有数据的日期（仅当未指定date时）
        if not items and not date:
            from sqlalchemy import func
            from app.models.fund_flow import ConceptFundFlow
            latest_date_with_data = db.query(func.max(ConceptFundFlow.date)).scalar()
            if latest_date_with_data and latest_date_with_data != target_date:
                items = FundFlowService.get_concept_fund_flow_db(db, latest_date_with_data, limit=limit)
        
        # 如果提供了概念名称，进行过滤
        if concept:
            items = [item for item in items if concept.lower() in (item.concept or '').lower()]
        
        # 转换为字典列表
        items_dict = []
        for item in items:
            item_dict = {
                column.name: getattr(item, column.name)
                for column in item.__table__.columns
            }
            items_dict.append(item_dict)
        
        return items_dict


@router.get("/industry")
def get_industry_fund_flow(
    date: str = Query(..., description="日期，格式YYYY-MM-DD"),
    limit: int = Query(200, ge=1, le=500, description="返回条数，默认200，最大500"),
    db: Session = Depends(get_db)
):
    """获取行业资金流（历史/当日），数据来自 daily sync 的 industry_fund_flow"""
    target_date = parse_date(date)
    if not target_date:
        raise HTTPException(status_code=400, detail="日期格式错误")
    items = FundFlowService.get_industry_fund_flow(db, target_date, limit=limit)
    return items


@router.post("/filter")
def filter_fund_flow(
    request: FundFlowFilterRequest,
    db: Session = Depends(get_db)
):
    """
    根据多个日期范围条件筛选资金流数据
    
    示例请求：
    ```json
    {
      "conditions": [
        {
          "date_range": {
            "start": "2026-01-10",
            "end": "2026-01-14"
          },
          "main_net_inflow": {
            "min": 100000000
          }
        },
        {
          "date_range": {
            "start": "2026-01-09",
            "end": "2026-01-14"
          },
          "main_net_inflow": {
            "max": 10000000
          }
        }
      ],
      "concept_ids": [1, 2],
      "page": 1,
      "page_size": 20
    }
    ```
    
    说明：
    - conditions: 筛选条件列表，多个条件之间是AND关系
    - 每个条件包含日期范围和主力净流入区间
    - 主力净流入单位：元（如 100000000 表示1亿，10000000 表示1000万）
    """
    try:
        items, total = FundFlowService.filter_fund_flow_by_conditions(
            db=db,
            conditions=request.conditions,
            concept_ids=request.concept_ids,
            concept_names=request.concept_names,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            order=request.order
        )
        
        return {
            "items": items,
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": math.ceil(total / request.page_size) if request.page_size > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选失败: {str(e)}")


@router.post("/concept/filter")
def filter_concept_fund_flow(
    request: ConceptFundFlowFilterRequest,
    db: Session = Depends(get_db)
):
    """
    多条件联合查询概念资金流
    
    示例请求：
    ```json
    {
      "conditions": [
        {
          "date_range": {
            "start": "2026-01-10",
            "end": "2026-01-14"
          },
          "net_amount": {
            "min": 100000000
          },
          "inflow": {
            "min": 500000000
          }
        },
        {
          "date_range": {
            "start": "2026-01-09",
            "end": "2026-01-13"
          },
          "net_amount": {
            "max": 50000000
          },
          "index_change_percent": {
            "min": 2.0
          }
        }
      ],
      "concepts": ["人工智能", "新能源"],
      "page": 1,
      "page_size": 20,
      "sort_by": "net_amount",
      "order": "desc"
    }
    ```
    
    说明：
    - conditions: 筛选条件列表，多个条件之间是AND关系（概念必须同时满足所有条件）
    - 每个条件包含日期范围和可选的各种数值区间条件
    - 净额、流入、流出单位：元（如 100000000 表示1亿）
    - 指数涨跌幅单位：%（如 2.0 表示2%）
    """
    try:
        items, total = FundFlowService.filter_concept_fund_flow_by_conditions(
            db=db,
            conditions=request.conditions,
            concepts=request.concepts,
            page=request.page,
            page_size=request.page_size,
            sort_by=request.sort_by,
            order=request.order
        )
        
        return {
            "items": items,
            "total": total,
            "page": request.page,
            "page_size": request.page_size,
            "total_pages": math.ceil(total / request.page_size) if request.page_size > 0 else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选失败: {str(e)}")

