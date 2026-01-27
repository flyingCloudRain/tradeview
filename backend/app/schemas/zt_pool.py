"""
涨停池Pydantic模式
"""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime, time
from decimal import Decimal


class ZtPoolBase(BaseModel):
    """涨停池基础模式"""
    date: date
    stock_code: str
    stock_name: str
    change_percent: Optional[Decimal] = None
    latest_price: Optional[Decimal] = None
    turnover_amount: Optional[int] = None
    circulation_market_value: Optional[Decimal] = None
    total_market_value: Optional[Decimal] = None
    turnover_rate: Optional[Decimal] = None
    limit_up_capital: Optional[int] = None
    first_limit_time: Optional[time] = None
    last_limit_time: Optional[time] = None
    explosion_count: Optional[int] = 0
    limit_up_statistics: Optional[str] = None
    consecutive_limit_count: Optional[int] = 1
    industry: Optional[str] = None
    concept: Optional[str] = None
    limit_up_reason: Optional[str] = None


class ZtPoolResponse(ZtPoolBase):
    """涨停池响应"""
    id: int
    created_at: datetime
    is_lhb: Optional[bool] = False  # 是否属于当日龙虎榜
    concepts: Optional[List[dict]] = None  # 概念板块列表
    limit_up_count: Optional[int] = None  # 涨停次数（日期范围查询时）
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """重写验证方法，支持从模型对象中提取概念板块（包含层级信息）"""
        if hasattr(obj, '_concepts'):
            # 如果有动态添加的概念板块，转换为字典列表（包含层级信息）
            concepts_data = [
                {
                    "id": c.id,
                    "name": c.name,
                    "code": c.code,
                    "level": c.level,
                    "parent_id": c.parent_id,
                    "path": c.path
                }
                for c in obj._concepts
            ]
            # 创建字典并添加concepts字段
            data = super().model_validate(obj, **kwargs).model_dump()
            data['concepts'] = concepts_data
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class ZtPoolListResponse(BaseModel):
    """涨停池列表响应"""
    items: List[ZtPoolResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ZtPoolUpdateRequest(BaseModel):
    """涨停池可编辑字段"""
    concept: Optional[str] = None
    limit_up_reason: Optional[str] = None


class ZtPoolAnalysisResponse(BaseModel):
    """涨停分析响应"""
    total_count: int
    industry_distribution: Dict[str, int]
    concept_distribution: Dict[str, int]
    reason_distribution: Dict[str, int]
    consecutive_limit_distribution: Dict[str, int]

