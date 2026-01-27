# 概念题材库层级设计方案

## 1. 需求分析

### 1.1 核心需求
- **层级结构**：支持 2-3 级层级模式
  - 一级：大类（如：科技、消费、金融等）
  - 二级：中类（如：人工智能、新能源汽车、银行等）
  - 三级：细分概念（如：ChatGPT、锂电池、数字货币等）
- **多对多关联**：个股可关联多个概念题材（支持跨层级）
- **层级查询**：支持按层级查询、统计、筛选
- **数据完整性**：保证层级关系的完整性和一致性

### 1.2 业务场景
- 按一级分类查看所有相关个股
- 按二级分类筛选特定行业个股
- 按三级概念精确匹配个股
- 统计各层级概念下的个股数量
- 查询概念的所有子概念和父概念

## 2. 数据库设计

### 2.1 概念题材表（支持层级）

```sql
CREATE TABLE stock_concept (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '概念板块名称',
    code VARCHAR(20) UNIQUE COMMENT '概念板块代码（可选）',
    description TEXT COMMENT '概念板块描述',
    
    -- 层级相关字段
    parent_id INTEGER NULL COMMENT '父概念ID，NULL表示一级概念',
    level INTEGER NOT NULL DEFAULT 1 COMMENT '层级：1=一级，2=二级，3=三级',
    path VARCHAR(500) COMMENT '层级路径，如：1/5/12，便于查询',
    sort_order INTEGER DEFAULT 0 COMMENT '同级排序顺序',
    
    -- 统计字段（可选，用于优化查询）
    stock_count INTEGER DEFAULT 0 COMMENT '关联的个股数量（冗余字段，用于快速统计）',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_id) REFERENCES stock_concept(id) ON DELETE SET NULL,
    CHECK (level IN (1, 2, 3)),
    CHECK ((parent_id IS NULL AND level = 1) OR (parent_id IS NOT NULL AND level > 1))
);

-- 索引
CREATE INDEX idx_concept_name ON stock_concept(name);
CREATE INDEX idx_concept_code ON stock_concept(code);
CREATE INDEX idx_concept_parent ON stock_concept(parent_id);
CREATE INDEX idx_concept_level ON stock_concept(level);
CREATE INDEX idx_concept_path ON stock_concept(path);
CREATE UNIQUE INDEX idx_concept_name_level ON stock_concept(name, level, parent_id);

COMMENT ON TABLE stock_concept IS '股票概念板块表（支持2-3级层级）';
```

### 2.2 层级结构示例

```
一级（level=1）
├── 科技类（id=1）
│   ├── 二级（level=2）
│   │   ├── 人工智能（id=5, parent_id=1）
│   │   │   ├── 三级（level=3）
│   │   │   │   ├── ChatGPT（id=12, parent_id=5）
│   │   │   │   ├── 机器学习（id=13, parent_id=5）
│   │   │   │   └── 计算机视觉（id=14, parent_id=5）
│   │   │   └── 5G通信（id=6, parent_id=1）
│   │   │       ├── 5G基站（id=15, parent_id=6）
│   │   │       └── 光通信（id=16, parent_id=6）
│   │   └── 新能源汽车（id=7, parent_id=1）
│   │       ├── 锂电池（id=17, parent_id=7）
│   │       └── 充电桩（id=18, parent_id=7）
│   └── 消费类（id=2）
│       └── 白酒（id=8, parent_id=2）
│           └── 高端白酒（id=19, parent_id=8）
```

### 2.3 股票概念关联表（保持不变）

```sql
CREATE TABLE stock_concept_mapping (
    id SERIAL PRIMARY KEY,
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    concept_id INTEGER NOT NULL COMMENT '概念板块ID（可以是任意层级）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stock_name, concept_id),
    FOREIGN KEY (concept_id) REFERENCES stock_concept(id) ON DELETE CASCADE
);

CREATE INDEX idx_scm_stock ON stock_concept_mapping(stock_name);
CREATE INDEX idx_scm_concept ON stock_concept_mapping(concept_id);

COMMENT ON TABLE stock_concept_mapping IS '股票概念板块关联表（支持关联任意层级的概念）';
```

**设计说明**：
- 个股可以关联任意层级的概念（一级、二级、三级都可以）
- 一个个股可以关联多个不同层级的概念
- 查询时可以通过层级路径自动包含子概念或父概念

## 3. 数据模型设计

### 3.1 Python/SQLAlchemy 模型

```python
# backend/app/models/stock_concept.py
from sqlalchemy import Column, String, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from app.database.base import BaseModel


class StockConcept(BaseModel):
    """股票概念板块表（支持2-3级层级）"""
    __tablename__ = "stock_concept"
    
    name = Column(String(100), nullable=False, comment="概念板块名称")
    code = Column(String(20), unique=True, nullable=True, comment="概念板块代码")
    description = Column(Text, nullable=True, comment="概念板块描述")
    
    # 层级相关字段
    parent_id = Column(Integer, ForeignKey('stock_concept.id', ondelete='SET NULL'), 
                       nullable=True, comment="父概念ID，NULL表示一级概念")
    level = Column(Integer, nullable=False, default=1, comment="层级：1=一级，2=二级，3=三级")
    path = Column(String(500), nullable=True, comment="层级路径，如：1/5/12")
    sort_order = Column(Integer, default=0, comment="同级排序顺序")
    
    # 统计字段（可选）
    stock_count = Column(Integer, default=0, comment="关联的个股数量")
    
    # 关联关系
    parent = relationship(
        "StockConcept",
        remote_side="StockConcept.id",
        backref="children"
    )
    
    stock_mappings = relationship(
        "StockConceptMapping",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    trading_calendar_mappings = relationship(
        "TradingCalendarConcept",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint('level IN (1, 2, 3)', name='check_level_range'),
        CheckConstraint(
            '(parent_id IS NULL AND level = 1) OR (parent_id IS NOT NULL AND level > 1)',
            name='check_level_parent'
        ),
        {"comment": "股票概念板块表（支持2-3级层级）"},
    )
    
    def get_full_path(self):
        """获取完整层级路径"""
        if self.path:
            return self.path.split('/')
        return []
    
    def get_all_ancestors(self):
        """获取所有祖先概念"""
        ancestors = []
        current = self.parent
        while current:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_all_descendants(self):
        """获取所有后代概念（递归）"""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants
```

### 3.2 Schema 设计

```python
# backend/app/schemas/stock_concept.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class StockConceptBase(BaseModel):
    name: str = Field(..., description="概念板块名称")
    code: Optional[str] = Field(None, description="概念板块代码")
    description: Optional[str] = Field(None, description="概念板块描述")
    parent_id: Optional[int] = Field(None, description="父概念ID")
    level: int = Field(1, ge=1, le=3, description="层级：1=一级，2=二级，3=三级")
    sort_order: int = Field(0, description="同级排序顺序")


class StockConceptCreate(StockConceptBase):
    pass


class StockConceptUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class StockConceptResponse(StockConceptBase):
    id: int
    path: Optional[str] = None
    stock_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockConceptTree(StockConceptResponse):
    """带子节点的树形结构"""
    children: List['StockConceptTree'] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class StockConceptWithStocks(StockConceptResponse):
    """带关联个股的概念"""
    stocks: List[str] = Field(default_factory=list, description="关联的股票名称列表")
```

## 4. API 设计

### 4.1 概念管理 API

```python
# backend/app/api/v1/stock_concept.py

@router.get("/concepts", response_model=List[StockConceptResponse])
async def list_concepts(
    level: Optional[int] = None,  # 按层级筛选
    parent_id: Optional[int] = None,  # 按父概念筛选
    db: Session = Depends(get_db)
):
    """获取概念列表"""
    pass


@router.get("/concepts/tree", response_model=List[StockConceptTree])
async def get_concept_tree(
    max_level: int = 3,  # 最大层级深度
    db: Session = Depends(get_db)
):
    """获取概念树形结构"""
    pass


@router.get("/concepts/{concept_id}", response_model=StockConceptResponse)
async def get_concept(
    concept_id: int,
    include_children: bool = False,  # 是否包含子概念
    include_stocks: bool = False,  # 是否包含关联个股
    db: Session = Depends(get_db)
):
    """获取概念详情"""
    pass


@router.post("/concepts", response_model=StockConceptResponse)
async def create_concept(
    concept: StockConceptCreate,
    db: Session = Depends(get_db)
):
    """创建概念"""
    pass


@router.put("/concepts/{concept_id}", response_model=StockConceptResponse)
async def update_concept(
    concept_id: int,
    concept: StockConceptUpdate,
    db: Session = Depends(get_db)
):
    """更新概念"""
    pass


@router.delete("/concepts/{concept_id}")
async def delete_concept(
    concept_id: int,
    cascade: bool = False,  # 是否级联删除子概念
    db: Session = Depends(get_db)
):
    """删除概念"""
    pass
```

### 4.2 层级查询 API

```python
@router.get("/concepts/{concept_id}/ancestors", response_model=List[StockConceptResponse])
async def get_ancestors(
    concept_id: int,
    db: Session = Depends(get_db)
):
    """获取所有祖先概念（向上查询）"""
    pass


@router.get("/concepts/{concept_id}/descendants", response_model=List[StockConceptResponse])
async def get_descendants(
    concept_id: int,
    include_self: bool = False,  # 是否包含自身
    db: Session = Depends(get_db)
):
    """获取所有后代概念（向下查询）"""
    pass


@router.get("/concepts/{concept_id}/stocks", response_model=List[str])
async def get_concept_stocks(
    concept_id: int,
    include_descendants: bool = True,  # 是否包含子概念的个股
    db: Session = Depends(get_db)
):
    """获取概念关联的所有个股（可包含子概念）"""
    pass
```

### 4.3 个股查询 API

```python
@router.get("/stocks/{stock_name}/concepts", response_model=List[StockConceptResponse])
async def get_stock_concepts(
    stock_name: str,
    level: Optional[int] = None,  # 按层级筛选
    db: Session = Depends(get_db)
):
    """获取个股关联的所有概念"""
    pass


@router.post("/stocks/{stock_name}/concepts")
async def add_stock_concepts(
    stock_name: str,
    concept_ids: List[int],  # 概念ID列表
    db: Session = Depends(get_db)
):
    """为个股添加概念关联"""
    pass


@router.delete("/stocks/{stock_name}/concepts/{concept_id}")
async def remove_stock_concept(
    stock_name: str,
    concept_id: int,
    db: Session = Depends(get_db)
):
    """移除个股的概念关联"""
    pass
```

## 5. 查询优化策略

### 5.1 Path 字段的使用

`path` 字段存储层级路径（如：`1/5/12`），便于：
- 快速查询某个概念的所有子概念：`WHERE path LIKE '1/5/%'`
- 快速查询某个概念的所有祖先：通过路径解析
- 快速排序：按路径自然排序即可得到层级顺序

### 5.2 查询示例

```sql
-- 1. 查询一级概念的所有子概念（包括二级和三级）
SELECT * FROM stock_concept 
WHERE path LIKE '1/%' OR path = '1';

-- 2. 查询某个二级概念的所有三级子概念
SELECT * FROM stock_concept 
WHERE parent_id = 5 AND level = 3;

-- 3. 查询某个概念关联的所有个股（包括子概念）
WITH RECURSIVE concept_tree AS (
    SELECT id FROM stock_concept WHERE id = 5
    UNION ALL
    SELECT sc.id FROM stock_concept sc
    INNER JOIN concept_tree ct ON sc.parent_id = ct.id
)
SELECT DISTINCT stock_name FROM stock_concept_mapping
WHERE concept_id IN (SELECT id FROM concept_tree);

-- 4. 统计各层级概念数量
SELECT level, COUNT(*) as count 
FROM stock_concept 
GROUP BY level 
ORDER BY level;
```

### 5.3 视图设计（可选）

```sql
-- 创建视图：概念树形结构
CREATE VIEW v_concept_tree AS
SELECT 
    c1.id as level1_id,
    c1.name as level1_name,
    c2.id as level2_id,
    c2.name as level2_name,
    c3.id as level3_id,
    c3.name as level3_name
FROM stock_concept c1
LEFT JOIN stock_concept c2 ON c2.parent_id = c1.id AND c2.level = 2
LEFT JOIN stock_concept c3 ON c3.parent_id = c2.id AND c3.level = 3
WHERE c1.level = 1;

-- 创建视图：概念统计（包含子概念个股数）
CREATE VIEW v_concept_statistics AS
SELECT 
    c.id,
    c.name,
    c.level,
    COUNT(DISTINCT scm.stock_name) as direct_stock_count,
    -- 这里可以添加递归查询统计所有子概念的个股数
    c.stock_count as total_stock_count
FROM stock_concept c
LEFT JOIN stock_concept_mapping scm ON scm.concept_id = c.id
GROUP BY c.id, c.name, c.level, c.stock_count;
```

## 6. 数据迁移方案

### 6.1 迁移步骤

1. **添加层级字段**
   ```sql
   ALTER TABLE stock_concept 
   ADD COLUMN parent_id INTEGER,
   ADD COLUMN level INTEGER DEFAULT 1,
   ADD COLUMN path VARCHAR(500),
   ADD COLUMN sort_order INTEGER DEFAULT 0,
   ADD COLUMN stock_count INTEGER DEFAULT 0;
   
   ALTER TABLE stock_concept 
   ADD CONSTRAINT fk_concept_parent 
   FOREIGN KEY (parent_id) REFERENCES stock_concept(id) ON DELETE SET NULL;
   ```

2. **初始化现有数据**
   - 将所有现有概念设置为一级（level=1）
   - 设置 path 为 id 值（如：`1`, `2`, `3`）

3. **建立层级关系**
   - 根据业务需求，将部分概念设置为二级或三级
   - 更新 parent_id 和 path

### 6.2 迁移脚本示例

```python
# backend/alembic/versions/add_concept_hierarchy.py
def upgrade():
    # 添加字段
    op.add_column('stock_concept', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('stock_concept', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('stock_concept', sa.Column('path', sa.String(500), nullable=True))
    op.add_column('stock_concept', sa.Column('sort_order', sa.Integer(), server_default='0'))
    op.add_column('stock_concept', sa.Column('stock_count', sa.Integer(), server_default='0'))
    
    # 添加外键
    op.create_foreign_key('fk_concept_parent', 'stock_concept', 'stock_concept', ['parent_id'], ['id'], ondelete='SET NULL')
    
    # 添加约束
    op.create_check_constraint('check_level_range', 'stock_concept', 'level IN (1, 2, 3)')
    op.create_check_constraint('check_level_parent', 'stock_concept', 
                               '(parent_id IS NULL AND level = 1) OR (parent_id IS NOT NULL AND level > 1)')
    
    # 初始化现有数据
    op.execute("""
        UPDATE stock_concept 
        SET level = 1, path = id::text 
        WHERE path IS NULL;
    """)
    
    # 创建索引
    op.create_index('idx_concept_parent', 'stock_concept', ['parent_id'])
    op.create_index('idx_concept_level', 'stock_concept', ['level'])
    op.create_index('idx_concept_path', 'stock_concept', ['path'])
```

## 7. 业务逻辑实现

### 7.1 创建概念时的处理

```python
def create_concept(db: Session, concept_data: StockConceptCreate):
    """创建概念，自动计算 path"""
    # 如果指定了 parent_id，验证父概念存在且层级正确
    if concept_data.parent_id:
        parent = db.query(StockConcept).filter(
            StockConcept.id == concept_data.parent_id
        ).first()
        if not parent:
            raise ValueError("父概念不存在")
        if parent.level >= concept_data.level:
            raise ValueError("层级设置错误")
        concept_data.level = parent.level + 1
    
    # 创建概念
    concept = StockConcept(**concept_data.dict())
    db.add(concept)
    db.flush()  # 获取 id
    
    # 计算 path
    if concept.parent_id:
        parent = db.query(StockConcept).filter(
            StockConcept.id == concept.parent_id
        ).first()
        concept.path = f"{parent.path}/{concept.id}"
    else:
        concept.path = str(concept.id)
    
    db.commit()
    return concept
```

### 7.2 更新概念时的处理

```python
def update_concept(db: Session, concept_id: int, update_data: StockConceptUpdate):
    """更新概念，如果修改了 parent_id，需要更新 path 和所有子概念的 path"""
    concept = db.query(StockConcept).filter(StockConcept.id == concept_id).first()
    
    if update_data.parent_id and update_data.parent_id != concept.parent_id:
        # 更新父概念
        old_path = concept.path
        concept.parent_id = update_data.parent_id
        
        # 重新计算 path
        parent = db.query(StockConcept).filter(
            StockConcept.id == concept.parent_id
        ).first()
        new_path = f"{parent.path}/{concept.id}"
        concept.path = new_path
        
        # 更新所有子概念的 path
        update_children_path(db, old_path, new_path)
    
    # 更新其他字段
    for key, value in update_data.dict(exclude_unset=True).items():
        setattr(concept, key, value)
    
    db.commit()
    return concept


def update_children_path(db: Session, old_path: str, new_path: str):
    """递归更新所有子概念的 path"""
    children = db.query(StockConcept).filter(
        StockConcept.path.like(f"{old_path}/%")
    ).all()
    
    for child in children:
        child.path = child.path.replace(old_path, new_path, 1)
        db.add(child)
    
    db.commit()
```

### 7.3 查询概念树

```python
def get_concept_tree(db: Session, max_level: int = 3):
    """获取概念树形结构"""
    # 查询所有一级概念
    level1_concepts = db.query(StockConcept).filter(
        StockConcept.level == 1
    ).order_by(StockConcept.sort_order, StockConcept.id).all()
    
    result = []
    for concept in level1_concepts:
        tree_node = build_tree_node(db, concept, max_level)
        result.append(tree_node)
    
    return result


def build_tree_node(db: Session, concept: StockConcept, max_level: int):
    """递归构建树节点"""
    node = StockConceptTree.from_orm(concept)
    
    if concept.level < max_level:
        # 查询子概念
        children = db.query(StockConcept).filter(
            StockConcept.parent_id == concept.id
        ).order_by(StockConcept.sort_order, StockConcept.id).all()
        
        node.children = [build_tree_node(db, child, max_level) for child in children]
    
    return node
```

## 8. 前端展示建议

### 8.1 树形组件

使用树形组件展示层级结构：
- 一级：根节点
- 二级：一级的子节点
- 三级：二级的子节点

### 8.2 筛选功能

- 按层级筛选：只显示一级/二级/三级
- 按父概念筛选：显示某个概念的所有子概念
- 按个股筛选：显示某个个股关联的所有概念

### 8.3 统计展示

- 显示每个概念关联的个股数量
- 显示每个一级概念下的二级、三级概念数量
- 显示每个概念在整个层级中的位置

## 9. 性能优化建议

1. **索引优化**：在 `parent_id`, `level`, `path` 上建立索引
2. **缓存策略**：缓存概念树结构，减少数据库查询
3. **批量查询**：使用 `IN` 查询替代多次单条查询
4. **统计字段**：使用 `stock_count` 冗余字段，避免实时统计
5. **分页查询**：对于大量概念，使用分页查询

## 10. 测试用例

### 10.1 单元测试

- 创建一级概念
- 创建二级概念（指定父概念）
- 创建三级概念（指定父概念）
- 更新概念的父概念（验证 path 更新）
- 删除概念（验证级联删除）

### 10.2 集成测试

- 查询概念树
- 查询某个概念的所有子概念
- 查询某个概念关联的所有个股
- 查询某个个股关联的所有概念

## 11. 总结

本设计方案实现了：
- ✅ 2-3 级层级结构支持
- ✅ 个股与概念的多对多关联
- ✅ 层级查询和统计功能
- ✅ 数据完整性保证
- ✅ 性能优化策略

该设计既保持了向后兼容（现有数据可以平滑迁移），又提供了灵活的层级管理能力。
