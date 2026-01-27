# 概念题材与现有个股接口集成方案

## 1. 集成目标

将层级概念题材功能集成到现有的个股相关接口中，实现：
- ✅ 支持按概念题材筛选个股
- ✅ 支持按层级筛选（一级/二级/三级）
- ✅ 支持包含子概念查询（查询某个概念时，自动包含其所有子概念）
- ✅ 在响应中返回个股关联的概念信息（包含层级信息）
- ✅ 保持向后兼容（不影响现有接口）

## 2. 涉及的现有接口

### 2.1 涨停池接口 (zt_pool)

**接口路径**: `/api/v1/zt-pool`

**当前支持的概念筛选参数**:
- `concept_ids`: 概念ID列表（逗号分隔）
- `concept_names`: 概念名称列表（逗号分隔）
- `concept`: 文本字段模糊匹配（兼容旧接口）

**响应字段**:
- `concepts`: 概念板块列表（已支持）

### 2.2 个股资金流接口 (stock-fund-flow)

**接口路径**: `/api/v1/stock-fund-flow`

**当前支持的概念筛选参数**:
- `concept_ids`: 概念ID列表（逗号分隔）
- `concept_names`: 概念名称列表（逗号分隔）

### 2.3 交易日历接口 (trading-calendar)

**接口路径**: `/api/v1/trading-calendar`

**当前支持的概念筛选参数**:
- 通过 `stock_name` 关联 `stock_concept_mapping`

### 2.4 涨停板分析接口 (limit-up-board)

**接口路径**: `/api/v1/limit-up-board`

**当前支持的概念筛选参数**:
- 通过 `stock_name` 关联概念

## 3. 增强方案

### 3.1 API 参数增强

#### 3.1.1 新增查询参数

为所有涉及概念筛选的接口添加以下参数：

```python
# 新增参数
concept_level: Optional[int] = Query(None, ge=1, le=3, description="概念层级筛选：1=一级，2=二级，3=三级")
include_descendants: bool = Query(True, description="是否包含子概念，True表示查询某个概念时自动包含其所有子概念")
include_ancestors: bool = Query(False, description="是否包含父概念，True表示查询某个概念时自动包含其所有父概念")
```

#### 3.1.2 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `concept_ids` | string | - | 概念ID列表（逗号分隔），如：`1,2,3` |
| `concept_names` | string | - | 概念名称列表（逗号分隔），如：`人工智能,新能源` |
| `concept_level` | int | - | 层级筛选：1=一级，2=二级，3=三级 |
| `include_descendants` | bool | true | 是否包含子概念 |
| `include_ancestors` | bool | false | 是否包含父概念 |

### 3.2 响应数据增强

#### 3.2.1 概念信息结构

在响应中返回的概念信息应包含层级信息：

```python
class ConceptInfo(BaseModel):
    """概念信息（带层级）"""
    id: int
    name: str
    code: Optional[str] = None
    level: int  # 新增：层级
    parent_id: Optional[int] = None  # 新增：父概念ID
    path: Optional[str] = None  # 新增：层级路径
```

#### 3.2.2 响应示例

```json
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "stock_code": "000001",
        "stock_name": "平安银行",
        "concepts": [
          {
            "id": 5,
            "name": "人工智能",
            "code": "AI",
            "level": 2,
            "parent_id": 1,
            "path": "1/5"
          },
          {
            "id": 12,
            "name": "ChatGPT",
            "code": "CHATGPT",
            "level": 3,
            "parent_id": 5,
            "path": "1/5/12"
          }
        ]
      }
    ]
  }
}
```

## 4. 服务层实现

### 4.1 概念查询工具函数

```python
# backend/app/services/stock_concept_service.py

class StockConceptService:
    """股票概念服务类"""
    
    @staticmethod
    def expand_concept_ids(
        db: Session,
        concept_ids: List[int],
        include_descendants: bool = True,
        include_ancestors: bool = False
    ) -> List[int]:
        """
        扩展概念ID列表（包含子概念或父概念）
        
        Args:
            db: 数据库会话
            concept_ids: 原始概念ID列表
            include_descendants: 是否包含子概念
            include_ancestors: 是否包含父概念
            
        Returns:
            扩展后的概念ID列表
        """
        if not concept_ids:
            return []
        
        expanded_ids = set(concept_ids)
        
        # 查询所有相关概念
        concepts = db.query(StockConcept).filter(
            StockConcept.id.in_(concept_ids)
        ).all()
        
        for concept in concepts:
            # 包含子概念
            if include_descendants:
                descendants = StockConceptService.get_all_descendant_ids(db, concept.id)
                expanded_ids.update(descendants)
            
            # 包含父概念
            if include_ancestors:
                ancestors = StockConceptService.get_all_ancestor_ids(db, concept.id)
                expanded_ids.update(ancestors)
        
        return list(expanded_ids)
    
    @staticmethod
    def get_all_descendant_ids(db: Session, concept_id: int) -> List[int]:
        """获取所有子概念ID（递归）"""
        descendant_ids = []
        
        # 查询直接子概念
        children = db.query(StockConcept).filter(
            StockConcept.parent_id == concept_id
        ).all()
        
        for child in children:
            descendant_ids.append(child.id)
            # 递归查询子概念的子概念
            descendant_ids.extend(
                StockConceptService.get_all_descendant_ids(db, child.id)
            )
        
        return descendant_ids
    
    @staticmethod
    def get_all_ancestor_ids(db: Session, concept_id: int) -> List[int]:
        """获取所有父概念ID（向上递归）"""
        ancestor_ids = []
        
        concept = db.query(StockConcept).filter(
            StockConcept.id == concept_id
        ).first()
        
        if concept and concept.parent_id:
            ancestor_ids.append(concept.parent_id)
            # 递归查询父概念的父概念
            ancestor_ids.extend(
                StockConceptService.get_all_ancestor_ids(db, concept.parent_id)
            )
        
        return ancestor_ids
    
    @staticmethod
    def get_stock_concepts_with_hierarchy(
        db: Session,
        stock_name: str
    ) -> List[StockConcept]:
        """
        获取个股关联的所有概念（包含层级信息）
        
        Args:
            db: 数据库会话
            stock_name: 股票名称
            
        Returns:
            概念列表（包含层级信息）
        """
        concepts = db.query(StockConcept).join(
            StockConceptMapping,
            StockConceptMapping.concept_id == StockConcept.id
        ).filter(
            StockConceptMapping.stock_name == stock_name
        ).order_by(
            StockConcept.level,
            StockConcept.sort_order,
            StockConcept.id
        ).all()
        
        return concepts
```

### 4.2 涨停池服务增强

```python
# backend/app/services/zt_pool_service.py

class ZtPoolService:
    """涨停池服务类"""
    
    @staticmethod
    def get_zt_pool_list(
        db: Session,
        target_date: date,
        stock_code: Optional[str] = None,
        concept: Optional[str] = None,
        industry: Optional[str] = None,
        consecutive_limit_count: Optional[int] = None,
        limit_up_statistics: Optional[str] = None,
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        concept_level: Optional[int] = None,  # 新增
        include_descendants: bool = True,  # 新增
        include_ancestors: bool = False,  # 新增
        is_lhb: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[ZtPool], int]:
        """
        获取涨停池列表（增强版）
        """
        query = db.query(ZtPool).filter(ZtPool.date == target_date)
        
        # ... 其他筛选条件 ...
        
        # 概念板块筛选（增强版）
        if concept_ids or concept_names or concept_level:
            # 扩展概念ID（包含子概念/父概念）
            final_concept_ids = []
            
            if concept_ids:
                # 扩展概念ID
                expanded_ids = StockConceptService.expand_concept_ids(
                    db=db,
                    concept_ids=concept_ids,
                    include_descendants=include_descendants,
                    include_ancestors=include_ancestors
                )
                final_concept_ids.extend(expanded_ids)
            
            if concept_names:
                # 根据名称查询概念ID
                name_concepts = db.query(StockConcept).filter(
                    StockConcept.name.in_(concept_names)
                ).all()
                name_concept_ids = [c.id for c in name_concepts]
                
                # 扩展概念ID
                expanded_ids = StockConceptService.expand_concept_ids(
                    db=db,
                    concept_ids=name_concept_ids,
                    include_descendants=include_descendants,
                    include_ancestors=include_ancestors
                )
                final_concept_ids.extend(expanded_ids)
            
            # 按层级筛选
            if concept_level is not None:
                level_concepts = db.query(StockConcept).filter(
                    StockConcept.level == concept_level
                )
                if final_concept_ids:
                    level_concepts = level_concepts.filter(
                        StockConcept.id.in_(final_concept_ids)
                    )
                final_concept_ids = [c.id for c in level_concepts.all()]
            
            # 去重
            final_concept_ids = list(set(final_concept_ids))
            
            if final_concept_ids:
                # 查询关联的股票名称
                concept_subquery = db.query(StockConceptMapping.stock_name).distinct().filter(
                    StockConceptMapping.concept_id.in_(final_concept_ids)
                )
                stock_names = [row[0] for row in concept_subquery.all()]
                
                if stock_names:
                    query = query.filter(ZtPool.stock_name.in_(stock_names))
                else:
                    query = query.filter(ZtPool.id == -1)
            else:
                query = query.filter(ZtPool.id == -1)
        
        # ... 其他逻辑 ...
        
        # 为每个涨停股添加概念信息（包含层级）
        for item in items:
            concepts = StockConceptService.get_stock_concepts_with_hierarchy(
                db=db,
                stock_name=item.stock_name
            )
            setattr(item, '_concepts', concepts)
        
        return items, total
```

### 4.3 资金流服务增强

```python
# backend/app/services/fund_flow_service.py

class FundFlowService:
    """资金流服务类"""
    
    @staticmethod
    def get_fund_flow_list(
        db: Session,
        target_date: date,
        stock_code: Optional[str] = None,
        concept_ids: Optional[List[int]] = None,
        concept_names: Optional[List[str]] = None,
        concept_level: Optional[int] = None,  # 新增
        include_descendants: bool = True,  # 新增
        include_ancestors: bool = False,  # 新增
        page: int = 1,
        page_size: int = 50,
        sort_by: Optional[str] = None,
        order: str = "desc"
    ) -> tuple[List[StockFundFlow], int]:
        """
        获取资金流列表（增强版）
        """
        query = db.query(StockFundFlow).filter(StockFundFlow.date == target_date)
        
        if stock_code:
            query = query.filter(StockFundFlow.stock_code == stock_code)
        
        # 概念板块筛选（增强版，与涨停池类似）
        if concept_ids or concept_names or concept_level:
            # ... 与涨停池服务类似的逻辑 ...
            pass
        
        # ... 其他逻辑 ...
        
        # 为每个资金流记录添加概念信息
        for item in items:
            concepts = StockConceptService.get_stock_concepts_with_hierarchy(
                db=db,
                stock_name=item.stock_name
            )
            setattr(item, '_concepts', concepts)
        
        return items, total
```

## 5. Schema 增强

### 5.1 概念信息 Schema

```python
# backend/app/schemas/stock_concept.py

class ConceptInfo(BaseModel):
    """概念信息（带层级）"""
    id: int
    name: str
    code: Optional[str] = None
    level: int = Field(..., description="层级：1=一级，2=二级，3=三级")
    parent_id: Optional[int] = Field(None, description="父概念ID")
    path: Optional[str] = Field(None, description="层级路径")
    
    class Config:
        from_attributes = True
```

### 5.2 响应 Schema 更新

```python
# backend/app/schemas/zt_pool.py

class ZtPoolResponse(ZtPoolBase):
    """涨停池响应"""
    id: int
    created_at: datetime
    is_lhb: Optional[bool] = False
    concepts: Optional[List[ConceptInfo]] = None  # 更新为带层级的概念信息
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """重写验证方法，支持从模型对象中提取概念板块（带层级）"""
        if hasattr(obj, '_concepts'):
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
            data = super().model_validate(obj, **kwargs).model_dump()
            data['concepts'] = concepts_data
            return cls(**data)
        return super().model_validate(obj, **kwargs)
```

## 6. API 接口更新

### 6.1 涨停池接口

```python
# backend/app/api/v1/zt_pool.py

@router.get("/", response_model=ZtPoolListResponse)
def get_zt_pool_list(
    date: str = Query(..., description="日期，格式：YYYY-MM-DD"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept: Optional[str] = Query(None, description="概念筛选（文本字段，兼容旧接口）"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    consecutive_limit_count: Optional[int] = Query(None, description="连板数筛选"),
    limit_up_statistics: Optional[str] = Query(None, description="板数筛选"),
    concept_ids: Optional[str] = Query(None, description="概念板块ID列表（逗号分隔）"),
    concept_names: Optional[str] = Query(None, description="概念板块名称列表（逗号分隔）"),
    concept_level: Optional[int] = Query(None, ge=1, le=3, description="概念层级筛选：1=一级，2=二级，3=三级"),  # 新增
    include_descendants: bool = Query(True, description="是否包含子概念"),  # 新增
    include_ancestors: bool = Query(False, description="是否包含父概念"),  # 新增
    is_lhb: Optional[bool] = Query(None, description="是否龙虎榜筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    sort_by: Optional[str] = Query(None, description="排序字段"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db)
):
    """获取涨停池列表（增强版）"""
    target_date = parse_date(date)
    if not target_date:
        raise HTTPException(status_code=400, detail="日期格式错误")
    
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
    
    items, total = ZtPoolService.get_zt_pool_list(
        db=db,
        target_date=target_date,
        stock_code=stock_code,
        concept=concept,
        industry=industry,
        consecutive_limit_count=consecutive_limit_count,
        limit_up_statistics=limit_up_statistics,
        concept_ids=concept_ids_list,
        concept_names=concept_names_list,
        concept_level=concept_level,  # 新增
        include_descendants=include_descendants,  # 新增
        include_ancestors=include_ancestors,  # 新增
        is_lhb=is_lhb,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order
    )
    
    total_pages = math.ceil(total / page_size)
    
    return ZtPoolListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
```

### 6.2 资金流接口

```python
# backend/app/api/v1/fund_flow.py

@router.get("/", response_model=StockFundFlowListResponse)
def get_fund_flow_list(
    date: str = Query(..., description="日期"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    concept_ids: Optional[str] = Query(None, description="概念板块ID列表（逗号分隔）"),
    concept_names: Optional[str] = Query(None, description="概念板块名称列表（逗号分隔）"),
    concept_level: Optional[int] = Query(None, ge=1, le=3, description="概念层级筛选"),  # 新增
    include_descendants: bool = Query(True, description="是否包含子概念"),  # 新增
    include_ancestors: bool = Query(False, description="是否包含父概念"),  # 新增
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
    sort_by: Optional[str] = Query("main_net_inflow"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db)
):
    """获取资金流列表（增强版）"""
    # ... 实现逻辑类似涨停池接口 ...
    pass
```

## 7. 使用示例

### 7.1 查询一级概念的所有个股

```http
GET /api/v1/zt-pool?date=2026-01-12&concept_level=1
```

### 7.2 查询某个概念及其所有子概念的个股

```http
GET /api/v1/zt-pool?date=2026-01-12&concept_ids=5&include_descendants=true
```

### 7.3 查询某个概念及其所有父概念的个股

```http
GET /api/v1/zt-pool?date=2026-01-12&concept_ids=12&include_ancestors=true
```

### 7.4 组合查询

```http
GET /api/v1/zt-pool?date=2026-01-12&concept_level=2&concept_names=人工智能,新能源&include_descendants=true
```

## 8. 性能优化

### 8.1 查询优化

1. **使用 path 字段快速查询子概念**
   ```sql
   -- 查询某个概念的所有子概念
   SELECT id FROM stock_concept 
   WHERE path LIKE '1/5/%' OR path = '1/5'
   ```

2. **批量查询概念关联**
   ```sql
   -- 批量查询多个股票的概念
   SELECT stock_name, concept_id, level, parent_id, path
   FROM stock_concept_mapping scm
   JOIN stock_concept sc ON scm.concept_id = sc.id
   WHERE scm.stock_name IN ('股票1', '股票2', '股票3')
   ```

3. **使用缓存**
   - 缓存概念树结构
   - 缓存概念扩展结果（concept_id -> expanded_ids）

### 8.2 索引优化

确保以下索引存在：
```sql
CREATE INDEX idx_concept_parent ON stock_concept(parent_id);
CREATE INDEX idx_concept_level ON stock_concept(level);
CREATE INDEX idx_concept_path ON stock_concept(path);
CREATE INDEX idx_scm_stock ON stock_concept_mapping(stock_name);
CREATE INDEX idx_scm_concept ON stock_concept_mapping(concept_id);
```

## 9. 向后兼容性

### 9.1 保持现有参数

- `concept_ids`: 继续支持
- `concept_names`: 继续支持
- `concept`: 文本字段模糊匹配（兼容旧接口）

### 9.2 默认行为

- `include_descendants`: 默认为 `true`，保持向后兼容
- `include_ancestors`: 默认为 `false`，不影响现有查询

### 9.3 响应格式

- 响应中的 `concepts` 字段增加层级信息，但不影响现有字段
- 如果概念没有层级信息（旧数据），`level` 默认为 1

## 10. 测试用例

### 10.1 单元测试

```python
def test_expand_concept_ids_with_descendants():
    """测试扩展概念ID（包含子概念）"""
    concept_ids = [5]  # 人工智能（二级）
    expanded = StockConceptService.expand_concept_ids(
        db=db,
        concept_ids=concept_ids,
        include_descendants=True
    )
    # 应该包含：5（人工智能）和所有三级子概念（如：12-ChatGPT, 13-机器学习等）
    assert 5 in expanded
    assert 12 in expanded
    assert 13 in expanded

def test_filter_by_concept_level():
    """测试按层级筛选"""
    items, total = ZtPoolService.get_zt_pool_list(
        db=db,
        target_date=date(2026, 1, 12),
        concept_level=1  # 只查询一级概念
    )
    # 验证所有返回的个股都关联了一级概念
    for item in items:
        assert any(c.level == 1 for c in item._concepts)
```

### 10.2 集成测试

```python
def test_zt_pool_api_with_hierarchy():
    """测试涨停池API（带层级）"""
    response = client.get("/api/v1/zt-pool", params={
        "date": "2026-01-12",
        "concept_level": 2,
        "include_descendants": True
    })
    assert response.status_code == 200
    data = response.json()
    # 验证响应中包含层级信息
    for item in data["data"]["items"]:
        if item["concepts"]:
            assert "level" in item["concepts"][0]
            assert "parent_id" in item["concepts"][0]
```

## 11. 实施步骤

1. **数据库迁移**
   - 添加层级字段到 `stock_concept` 表
   - 创建索引

2. **服务层实现**
   - 实现概念扩展函数
   - 更新服务层查询逻辑

3. **Schema 更新**
   - 添加 `ConceptInfo` schema
   - 更新响应 schema

4. **API 更新**
   - 添加新参数
   - 更新接口逻辑

5. **测试**
   - 单元测试
   - 集成测试
   - 性能测试

6. **文档更新**
   - API 文档
   - 使用示例

## 12. 总结

本方案实现了：
- ✅ 层级概念题材与现有接口的完整集成
- ✅ 支持按层级筛选和包含子概念/父概念查询
- ✅ 响应中包含完整的层级信息
- ✅ 保持向后兼容
- ✅ 性能优化策略

该方案可以逐步实施，不影响现有功能，同时为未来扩展提供了良好的基础。
