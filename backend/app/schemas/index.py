"""
大盘指数响应Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from decimal import Decimal


class IndexResponse(BaseModel):
    """指数响应"""
    id: int
    date: date
    index_code: str
    index_name: str
    close_price: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    volume: Optional[int] = None
    amount: Optional[Decimal] = None
    volume_change_percent: Optional[float] = Field(None, description="成交量变化比例（相比前一交易日）")
    
    class Config:
        from_attributes = True

