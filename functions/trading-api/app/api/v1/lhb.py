"""
龙虎榜API路由
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import math

from app.database.session import get_db
from app.services.lhb_service import LhbService
from app.services.lhb_hot_service import LhbHotService
from app.services.trader_service import TraderService
from app.schemas.lhb import (
    LhbListResponse,
    LhbDetailFullResponse,
    LhbDetailResponse,
    LhbInstitutionResponse,
    LhbHotInstitutionResponse,
    LhbHotListResponse,
    LhbInstitutionItemResponse,
    LhbHotInstitutionDetailResponse,
    TraderResponse,
)
from app.utils.date_utils import parse_date
from app.config import settings

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
    import logging
    import sys
    logger = logging.getLogger(__name__)
    
    # 打印到控制台（用于调试）
    print(f"[LHB API] 收到请求: date={date} (type: {type(date)}), stock_code={stock_code}, stock_name={stock_name}, page={page}, page_size={page_size}")
    sys.stdout.flush()
    
    target_date = parse_date(date)
    if not target_date:
        print(f"[LHB API] 日期解析失败: {date}")
        sys.stdout.flush()
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="日期格式错误")
    
    print(f"[LHB API] 解析后的日期: {target_date} (type: {type(target_date)})")
    sys.stdout.flush()
    
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
    
    print(f"[LHB API] 查询结果: {len(items)} 条, total: {total}")
    if len(items) > 0:
        print(f"[LHB API] 第一条数据: {items[0].stock_name} ({items[0].stock_code})")
    else:
        print(f"[LHB API] ⚠️  查询结果为空，检查数据库...")
        # 检查数据库中是否有该日期的数据
        from app.models.lhb import LhbDetail
        db_count = db.query(LhbDetail).filter(LhbDetail.date == target_date).count()
        print(f"[LHB API] 数据库中该日期的数据数量: {db_count}")
    sys.stdout.flush()
    
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
                print(f"[LHB API] 查询机构数据失败: {str(e)}")
                import traceback
                traceback.print_exc()
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
                print(f"[LHB API] 处理股票 {item.stock_code} {item.stock_name} 失败: {str(e)}")
                import traceback
                traceback.print_exc()
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
                    print(f"[LHB API] 跳过股票 {item.stock_code} {item.stock_name}")
                    continue
    except Exception as e:
        print(f"[LHB API] 处理机构信息失败: {str(e)}")
        import traceback
        traceback.print_exc()
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
    
    print(f"[LHB API] 返回响应: items={len(response.items)}, total={response.total}")
    sys.stdout.flush()
    
    return response


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
    import math
    import sys
    from fastapi import HTTPException
    
    try:
        target_date = parse_date(date) if date else None
        print(f"[LHB Institution API] 收到请求: date={date}, target_date={target_date}, page={page}, page_size={page_size}, flag={flag}, stock_name={stock_name}, stock_code={stock_code}")
        sys.stdout.flush()
        
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
        
        print(f"[LHB Institution API] 查询返回: {len(items)} 条items, total: {total}")
        sys.stdout.flush()
        
        # 转换为响应对象，包含股票名称
        def safe_float(value):
            """安全转换为float，处理inf、-inf、NaN等异常值"""
            import math
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
                print(f"[LHB Institution API] 转换第 {idx+1} 条数据失败: {str(e)}")
                print(f"[LHB Institution API] 数据内容: id={item.id}, stock_code={item.stock_code}, institution_name={item.institution_name}")
                print(f"[LHB Institution API] buy_amount类型: {type(item.buy_amount)}, 值: {item.buy_amount}")
                import traceback
                traceback.print_exc()
                sys.stdout.flush()
                continue
        
        print(f"[LHB Institution API] 返回结果: {len(response_items)} 条, total: {total}")
        if len(response_items) > 0:
            print(f"[LHB Institution API] 第一条数据: {response_items[0].institution_name}, 股票: {response_items[0].stock_name}, 方向: {response_items[0].flag}")
        sys.stdout.flush()
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return LhbHotListResponse(
            items=response_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    except Exception as e:
        print(f"[LHB Institution API] 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
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


@router.get("/traders", response_model=list[TraderResponse])
def list_traders(db: Session = Depends(get_db)):
    """游资主体及营业部列表（极简）"""
    traders = TraderService.list_traders(db)
    return traders


@router.get("/traders/lookup", response_model=Optional[TraderResponse])
def lookup_trader(
    institution_code: Optional[str] = Query(None, description="营业部代码"),
    institution_name: Optional[str] = Query(None, description="营业部名称"),
    db: Session = Depends(get_db)
):
    """通过营业部代码/名称反查游资"""
    trader = TraderService.get_trader_by_institution(
        db=db,
        institution_code=institution_code,
        institution_name=institution_name,
    )
    return trader


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

