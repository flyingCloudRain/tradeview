"""
交易日历Pydantic模式
"""
from pydantic import BaseModel, Field, field_validator, field_serializer, ConfigDict
from typing import Optional, List
from datetime import date as dt_date, datetime


class TradingCalendarBase(BaseModel):
    """交易日历基础模式"""
    model_config = ConfigDict(from_attributes=True)
    
    date: dt_date
    stock_name: str = Field(..., min_length=1, max_length=50, description="股票名称")
    direction: str = Field(..., description="操作方向：买入/卖出")
    strategy: str = Field(..., description="策略：低吸/排板")
    price: Optional[float] = Field(None, ge=0, description="价格")
    is_executed: Optional[bool] = Field(None, description="是否执行策略")
    source: Optional[str] = Field(None, max_length=100, description="来源")
    notes: Optional[str] = Field(None, description="备注")
    images: Optional[List[str]] = Field(None, description="图片URL列表")
    
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """解析日期字符串"""
        if v is None or v == '':
            raise ValueError('日期不能为空')
        if isinstance(v, str):
            from datetime import datetime
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f'日期格式错误: {v}，应为 YYYY-MM-DD')
        return v
    
    @field_validator('direction')
    @classmethod
    def validate_direction(cls, v):
        if v not in ['买入', '卖出']:
            raise ValueError('操作方向必须是"买入"或"卖出"')
        return v
    
    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        if v not in ['低吸', '排板']:
            raise ValueError('策略必须是"低吸"或"排板"')
        return v
    
    @field_serializer('date')
    def serialize_date(self, value: dt_date, _info) -> str:
        """序列化日期为字符串"""
        if value is None:
            return None
        return value.isoformat()


class TradingCalendarCreate(TradingCalendarBase):
    """创建交易日历"""
    pass


class TradingCalendarUpdate(BaseModel):
    """更新交易日历"""
    model_config = ConfigDict(from_attributes=True)
    
    date: Optional[dt_date] = None
    stock_name: Optional[str] = None
    direction: Optional[str] = None
    strategy: Optional[str] = None
    price: Optional[float] = None
    is_executed: Optional[bool] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    images: Optional[List[str]] = None
    
    @field_validator('date', mode='before')
    @classmethod
    def parse_date(cls, v):
        """解析日期字符串"""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            from datetime import datetime
            try:
                return datetime.strptime(v, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError(f'日期格式错误: {v}，应为 YYYY-MM-DD')
        return v
    
    @field_validator('stock_name', mode='before')
    @classmethod
    def validate_stock_name(cls, v):
        """处理空字符串"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        if v and isinstance(v, str) and len(v.strip()) > 50:
            raise ValueError('股票名称不能超过50个字符')
        return v.strip() if isinstance(v, str) else v
    
    @field_validator('direction')
    @classmethod
    def validate_direction(cls, v):
        if v is not None and v not in ['买入', '卖出']:
            raise ValueError('操作方向必须是"买入"或"卖出"')
        return v
    
    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v):
        if v is not None and v not in ['低吸', '排板']:
            raise ValueError('策略必须是"低吸"或"排板"')
        return v
    
    @field_validator('source', mode='before')
    @classmethod
    def validate_source(cls, v):
        """处理来源字段"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        if v and isinstance(v, str):
            v = v.strip()
            if len(v) > 100:
                raise ValueError('来源不能超过100个字符')
        return v
    
    @field_validator('notes', mode='before')
    @classmethod
    def validate_notes(cls, v):
        """处理备注字段"""
        if v == '' or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip() if isinstance(v, str) else v


class TradingCalendarResponse(TradingCalendarBase):
    """交易日历响应"""
    id: int
    created_at: datetime
    
    @field_serializer('created_at', when_used='json')
    def serialize_datetime(self, value: datetime, _info) -> str:
        """序列化日期时间为字符串"""
        if value is None:
            return None
        return value.isoformat()


class TradingCalendarListResponse(BaseModel):
    """交易日历列表响应"""
    items: list[TradingCalendarResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

