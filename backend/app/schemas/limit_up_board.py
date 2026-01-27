"""
涨停板分析Pydantic模式
"""
from pydantic import BaseModel, Field, field_validator, field_serializer, model_validator
from typing import Optional, List, Tuple
from datetime import date as dt_date, datetime, time as dt_time


def parse_keywords_to_tags(keywords: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """
    解析关键字为涨停原因和标签列表
    返回: (涨停原因, 标签列表)
    """
    if not keywords or not keywords.strip():
        return None, []
    
    # 使用 "+" 分割关键字
    parts = [part.strip() for part in keywords.split('+') if part.strip()]
    
    if not parts:
        return None, []
    
    # 第一个关键字作为主要涨停原因
    limit_up_reason = parts[0] if parts else None
    
    # 所有关键字作为标签
    tags = parts
    
    return limit_up_reason, tags


def extract_concept_names_from_keywords(keywords: Optional[str], existing_concepts: List[str]) -> List[str]:
    """
    从关键字中提取概念板块名称
    通过匹配现有概念板块名称来提取
    """
    if not keywords or not keywords.strip():
        return []
    
    found_concepts = []
    keywords_lower = keywords.lower()
    
    # 遍历现有概念板块，检查是否在关键字中出现
    for concept in existing_concepts:
        if concept.lower() in keywords_lower:
            found_concepts.append(concept)
    
    return found_concepts


class LimitUpBoardBase(BaseModel):
    """涨停板分析基础模式"""
    model_config = {"from_attributes": True}
    
    date: dt_date
    board_name: str = Field(..., min_length=1, max_length=100, description="板块名称")
    board_stock_count: Optional[int] = Field(None, ge=0, description="板块股票数量")
    stock_code: str = Field(..., min_length=1, max_length=20, description="股票代码")
    stock_name: str = Field(..., min_length=1, max_length=50, description="股票名称")
    limit_up_days: Optional[str] = Field(None, max_length=20, description="涨停天数（如：11 天 9 板）")
    limit_up_time: Optional[dt_time] = Field(None, description="涨停时间")
    circulation_market_value: Optional[float] = Field(None, ge=0, description="流通市值（亿元）")
    turnover_amount: Optional[float] = Field(None, ge=0, description="成交额（亿元）")
    keywords: Optional[str] = Field(None, description="涨停关键词（原始文本）")
    limit_up_reason: Optional[str] = Field(None, description="涨停原因（解析后的主要原因）")
    tags: Optional[List[str]] = Field(None, description="涨停标签列表（从关键字解析）")
    
    # 新增字段
    price_change_pct: Optional[float] = Field(None, description="涨跌幅（%，单位：%）")
    latest_price: Optional[float] = Field(None, ge=0, description="最新价")
    turnover: Optional[int] = Field(None, ge=0, description="成交额")
    total_market_value: Optional[float] = Field(None, ge=0, description="总市值（亿元）")
    turnover_rate: Optional[float] = Field(None, ge=0, description="换手率（%，单位：%）")
    sealing_capital: Optional[int] = Field(None, ge=0, description="封板资金")
    first_sealing_time: Optional[dt_time] = Field(None, description="首次封板时间（格式：09:25:00）")
    last_sealing_time: Optional[dt_time] = Field(None, description="最后封板时间（格式：09:25:00）")
    board_breaking_count: Optional[int] = Field(None, ge=0, description="炸板次数")
    limit_up_statistics: Optional[str] = Field(None, max_length=100, description="涨停统计")
    consecutive_board_count: Optional[int] = Field(None, ge=1, description="连板数（1为首板）")
    industry: Optional[str] = Field(None, max_length=100, description="所属行业")
    
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
    
    @field_validator('limit_up_time', 'first_sealing_time', 'last_sealing_time', mode='before')
    @classmethod
    def parse_time(cls, v):
        """解析时间字符串"""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                # 支持 HH:MM:SS 格式
                from datetime import datetime
                return datetime.strptime(v, "%H:%M:%S").time()
            except ValueError:
                return None
        return v
    
    @model_validator(mode='after')
    def parse_keywords(self):
        """自动解析关键字为标签和涨停原因"""
        if self.keywords and not self.tags:
            reason, tags = parse_keywords_to_tags(self.keywords)
            if reason:
                self.limit_up_reason = reason
            if tags:
                self.tags = tags
        return self
    
    @field_serializer('date')
    def serialize_date(self, value: dt_date, _info) -> str:
        """序列化日期为字符串"""
        return value.strftime("%Y-%m-%d") if value else None
    
    @field_serializer('limit_up_time', 'first_sealing_time', 'last_sealing_time')
    def serialize_time(self, value: dt_time, _info) -> str:
        """序列化时间为字符串"""
        return value.strftime("%H:%M:%S") if value else None


class LimitUpBoardCreate(LimitUpBoardBase):
    """创建涨停板分析"""
    concept_names: Optional[List[str]] = Field(None, description="概念板块名称列表（可选，会自动从关键字解析）")


class LimitUpBoardUpdate(BaseModel):
    """更新涨停板分析"""
    board_name: Optional[str] = Field(None, min_length=1, max_length=100)
    board_stock_count: Optional[int] = Field(None, ge=0)
    stock_code: Optional[str] = Field(None, min_length=1, max_length=20)
    stock_name: Optional[str] = Field(None, min_length=1, max_length=50)
    limit_up_days: Optional[str] = Field(None, max_length=20)
    limit_up_time: Optional[dt_time] = None
    circulation_market_value: Optional[float] = Field(None, ge=0)
    turnover_amount: Optional[float] = Field(None, ge=0)
    keywords: Optional[str] = None
    limit_up_reason: Optional[str] = None
    tags: Optional[List[str]] = None
    concept_names: Optional[List[str]] = None
    
    # 新增字段
    price_change_pct: Optional[float] = Field(None, description="涨跌幅（%，单位：%）")
    latest_price: Optional[float] = Field(None, ge=0)
    turnover: Optional[int] = Field(None, ge=0)
    total_market_value: Optional[float] = Field(None, ge=0)
    turnover_rate: Optional[float] = Field(None, ge=0, description="换手率（%，单位：%）")
    sealing_capital: Optional[int] = Field(None, ge=0)
    first_sealing_time: Optional[dt_time] = None
    last_sealing_time: Optional[dt_time] = None
    board_breaking_count: Optional[int] = Field(None, ge=0)
    limit_up_statistics: Optional[str] = Field(None, max_length=100)
    consecutive_board_count: Optional[int] = Field(None, ge=1)
    industry: Optional[str] = Field(None, max_length=100)
    
    @field_validator('limit_up_time', 'first_sealing_time', 'last_sealing_time', mode='before')
    @classmethod
    def parse_time(cls, v):
        """解析时间字符串"""
        if v is None or v == '':
            return None
        if isinstance(v, str):
            try:
                from datetime import datetime
                return datetime.strptime(v, "%H:%M:%S").time()
            except ValueError:
                return None
        return v
    
    @model_validator(mode='after')
    def parse_keywords(self):
        """自动解析关键字为标签和涨停原因"""
        if self.keywords and not self.tags:
            reason, tags = parse_keywords_to_tags(self.keywords)
            if reason:
                self.limit_up_reason = reason
            if tags:
                self.tags = tags
        return self


class LimitUpBoardResponse(LimitUpBoardBase):
    """涨停板分析响应"""
    id: int
    created_at: datetime
    concepts: Optional[List[dict]] = Field(None, description="关联的概念板块列表")
    
    model_config = {"from_attributes": True}
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """重写验证方法，支持从模型对象中提取概念板块"""
        if hasattr(obj, '_concepts'):
            # 如果有动态添加的概念板块，转换为字典列表
            concepts_data = [
                {"id": c.id, "name": c.name, "code": c.code}
                for c in obj._concepts
            ]
            # 创建字典并添加concepts字段
            data = super().model_validate(obj, **kwargs).model_dump()
            data['concepts'] = concepts_data
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class LimitUpBoardListResponse(BaseModel):
    """涨停板分析列表响应"""
    items: List[LimitUpBoardResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class LimitUpBoardListParams(BaseModel):
    """涨停板分析列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    date: Optional[str] = Field(None, description="日期 (YYYY-MM-DD)")
    board_name: Optional[str] = Field(None, description="板块名称")
    stock_code: Optional[str] = Field(None, description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称（模糊查询）")
    tag: Optional[str] = Field(None, description="标签筛选（模糊查询）")
    limit_up_reason: Optional[str] = Field(None, description="涨停原因筛选（模糊查询）")
    concept_id: Optional[int] = Field(None, description="概念板块ID筛选")
    concept_name: Optional[str] = Field(None, description="概念板块名称筛选")


class LimitUpBoardBatchCreate(BaseModel):
    """批量创建涨停板分析"""
    date: dt_date
    items: List[LimitUpBoardCreate] = Field(..., min_length=1, description="涨停板分析列表")
    auto_extract_concepts: bool = Field(True, description="是否自动从关键字提取概念板块")
    
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
