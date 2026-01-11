# 股票概念板块功能设计方案

## 1. 需求分析

在系统中增加股票概念板块功能，实现：
- **统一管理**：建立股票名称与概念板块的通用关联关系
- **多模块支持**：在以下三个模块中体现概念板块
  - 涨停榜个股信息（zt_pool）
  - 个股资金流（stock_fund_flow）
  - 交易日历（trading_calendar）
- **多对多关系**：支持一个股票关联多个概念板块
- **筛选功能**：支持按概念板块筛选各模块数据
- **管理功能**：支持概念板块的增删改查管理

## 2. 数据库设计

### 2.1 概念板块表 (stock_concept)

存储概念板块的基础信息。

```sql
CREATE TABLE stock_concept (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '概念板块名称',
    code VARCHAR(20) UNIQUE COMMENT '概念板块代码（可选）',
    description TEXT COMMENT '概念板块描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_concept_name ON stock_concept(name);
CREATE INDEX idx_concept_code ON stock_concept(code);
COMMENT ON TABLE stock_concept IS '股票概念板块表';
```

### 2.2 股票概念关联表 (trading_calendar_concept)

交易日历与概念板块的多对多关联表。

```sql
CREATE TABLE trading_calendar_concept (
    id SERIAL PRIMARY KEY,
    trading_calendar_id INTEGER NOT NULL COMMENT '交易日历ID',
    concept_id INTEGER NOT NULL COMMENT '概念板块ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trading_calendar_id, concept_id),
    FOREIGN KEY (trading_calendar_id) REFERENCES trading_calendar(id) ON DELETE CASCADE,
    FOREIGN KEY (concept_id) REFERENCES stock_concept(id) ON DELETE CASCADE
);

CREATE INDEX idx_tcc_calendar ON trading_calendar_concept(trading_calendar_id);
CREATE INDEX idx_tcc_concept ON trading_calendar_concept(concept_id);
COMMENT ON TABLE trading_calendar_concept IS '交易日历概念板块关联表';
```

### 2.3 股票概念通用关联表 (stock_concept_mapping) ⭐核心表

**重要**：这是核心关联表，建立股票名称与概念板块的通用关联关系，供所有模块使用。

```sql
CREATE TABLE stock_concept_mapping (
    id SERIAL PRIMARY KEY,
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    concept_id INTEGER NOT NULL COMMENT '概念板块ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_name, concept_id),
    FOREIGN KEY (concept_id) REFERENCES stock_concept(id) ON DELETE CASCADE
);

CREATE INDEX idx_scm_stock ON stock_concept_mapping(stock_name);
CREATE INDEX idx_scm_concept ON stock_concept_mapping(concept_id);
COMMENT ON TABLE stock_concept_mapping IS '股票概念板块通用关联表（核心表，供所有模块使用）';
```

**设计说明**：
- 此表作为**统一数据源**，所有模块通过股票名称查询概念板块
- 避免数据冗余，一个股票的概念板块只需维护一次
- 支持通过视图或关联查询在三个模块中展示概念板块

### 2.4 模块关联说明

**不需要为每个模块单独创建关联表**，而是通过以下方式关联：

1. **涨停榜（zt_pool）**：通过 `stock_name` 关联 `stock_concept_mapping`
2. **个股资金流（stock_fund_flow）**：通过 `stock_name` 关联 `stock_concept_mapping`
3. **交易日历（trading_calendar）**：通过 `stock_name` 关联 `stock_concept_mapping`

**可选：交易日历专用关联表（trading_calendar_concept）**

如果需要为交易日历中的特定记录覆盖或补充概念板块（不依赖股票名称），可以保留此表：

```sql
CREATE TABLE trading_calendar_concept (
    id SERIAL PRIMARY KEY,
    trading_calendar_id INTEGER NOT NULL COMMENT '交易日历ID',
    concept_id INTEGER NOT NULL COMMENT '概念板块ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trading_calendar_id, concept_id),
    FOREIGN KEY (trading_calendar_id) REFERENCES trading_calendar(id) ON DELETE CASCADE,
    FOREIGN KEY (concept_id) REFERENCES stock_concept(id) ON DELETE CASCADE
);

CREATE INDEX idx_tcc_calendar ON trading_calendar_concept(trading_calendar_id);
CREATE INDEX idx_tcc_concept ON trading_calendar_concept(concept_id);
COMMENT ON TABLE trading_calendar_concept IS '交易日历概念板块关联表（可选，用于覆盖或补充）';
```

**查询逻辑**：
- 优先使用 `trading_calendar_concept` 中的概念板块
- 如果没有，则从 `stock_concept_mapping` 中根据 `stock_name` 查询

## 3. 数据模型设计

### 3.1 后端模型 (Python/SQLAlchemy)

#### 3.1.1 StockConcept 模型

```python
# backend/app/models/stock_concept.py
from sqlalchemy import Column, String, Text, relationship
from sqlalchemy.orm import relationship
from app.database.base import BaseModel

class StockConcept(BaseModel):
    """股票概念板块表"""
    __tablename__ = "stock_concept"
    
    name = Column(String(100), nullable=False, unique=True, comment="概念板块名称")
    code = Column(String(20), unique=True, nullable=True, comment="概念板块代码")
    description = Column(Text, nullable=True, comment="概念板块描述")
    
    # 关联关系
    stock_mappings = relationship(
        "StockConceptMapping",
        back_populates="concept",
        cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        {"comment": "股票概念板块表"},
    )
```

#### 3.1.2 StockConceptMapping 模型（核心关联表）

```python
# backend/app/models/stock_concept.py
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import BaseModel

class StockConceptMapping(BaseModel):
    """股票概念板块通用关联表"""
    __tablename__ = "stock_concept_mapping"
    
    stock_name = Column(String(50), nullable=False, index=True, comment="股票名称")
    concept_id = Column(Integer, ForeignKey('stock_concept.id', ondelete='CASCADE'), nullable=False, index=True)
    
    # 关联关系
    concept = relationship("StockConcept", back_populates="stock_mappings")
    
    __table_args__ = (
        {"comment": "股票概念板块通用关联表"},
        {"unique": ("stock_name", "concept_id")}
    )
```

#### 3.1.3 扩展各模块模型

**交易日历模型扩展**：

```python
# backend/app/models/trading_calendar.py
from sqlalchemy.orm import relationship
from sqlalchemy import select

class TradingCalendar(BaseModel):
    """交易日历表"""
    __tablename__ = "trading_calendar"
    
    # ... 现有字段 ...
    
    # 通过股票名称关联概念板块（动态属性）
    @property
    def concepts(self):
        """通过股票名称获取概念板块"""
        from app.models.stock_concept import StockConceptMapping, StockConcept
        # 这里需要在查询时使用 joinedload 或手动查询
        # 实际实现中应该使用 relationship 或查询时 join
        pass
    
    # 或者使用 hybrid_property 或 relationship（需要额外配置）
```

**涨停榜模型扩展**：

```python
# backend/app/models/zt_pool.py
class ZtPool(BaseModel):
    """涨停池表"""
    __tablename__ = "zt_pool"
    
    # ... 现有字段 ...
    # 注意：现有 concept 字段（Text）可以保留用于兼容，但建议使用关联表
    
    # 通过股票名称关联概念板块
    # 实现方式同 TradingCalendar
```

**个股资金流模型扩展**：

```python
# backend/app/models/fund_flow.py
class StockFundFlow(BaseModel):
    """个股资金流表"""
    __tablename__ = "stock_fund_flow"
    
    # ... 现有字段 ...
    
    # 通过股票名称关联概念板块
    # 实现方式同 TradingCalendar
```

**推荐实现方式**：使用 SQLAlchemy 的 `hybrid_property` 或查询时手动 join，避免复杂的多对多关系配置。

## 4. API 设计

### 4.1 概念板块管理 API

#### 4.1.1 获取概念板块列表

```
GET /api/v1/stock-concepts
Query Parameters:
  - page: int (default: 1)
  - page_size: int (default: 20)
  - name: string (模糊搜索)
  - code: string (精确搜索)

Response:
{
  "items": [
    {
      "id": 1,
      "name": "人工智能",
      "code": "AI",
      "description": "人工智能相关概念",
      "created_at": "2026-01-11T10:00:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

#### 4.1.2 创建概念板块

```
POST /api/v1/stock-concepts
Request Body:
{
  "name": "人工智能",
  "code": "AI",
  "description": "人工智能相关概念"
}

Response:
{
  "id": 1,
  "name": "人工智能",
  "code": "AI",
  "description": "人工智能相关概念",
  "created_at": "2026-01-11T10:00:00Z"
}
```

#### 4.1.3 更新概念板块

```
PUT /api/v1/stock-concepts/{concept_id}
Request Body:
{
  "name": "人工智能",
  "code": "AI",
  "description": "更新后的描述"
}
```

#### 4.1.4 删除概念板块

```
DELETE /api/v1/stock-concepts/{concept_id}
Response: 204 No Content
```

### 4.2 交易日历概念板块关联 API

#### 4.2.1 为交易日历添加概念板块

```
POST /api/v1/trading-calendar/{calendar_id}/concepts
Request Body:
{
  "concept_ids": [1, 2, 3]
}

Response:
{
  "trading_calendar_id": 123,
  "concepts": [
    {"id": 1, "name": "人工智能"},
    {"id": 2, "name": "新能源"},
    {"id": 3, "name": "5G"}
  ]
}
```

#### 4.2.2 更新交易日历的概念板块

```
PUT /api/v1/trading-calendar/{calendar_id}/concepts
Request Body:
{
  "concept_ids": [1, 2]  // 替换所有关联
}
```

#### 4.2.3 删除交易日历的概念板块关联

```
DELETE /api/v1/trading-calendar/{calendar_id}/concepts/{concept_id}
Response: 204 No Content
```

### 4.3 各模块查询扩展

#### 4.3.1 交易日历按概念板块筛选

```
GET /api/v1/trading-calendar
Query Parameters:
  - concept_ids: string (逗号分隔，如 "1,2,3")
  - concept_names: string (逗号分隔，如 "人工智能,新能源")
  - ... 其他现有参数

Response: 扩展现有响应，包含 concepts 字段
{
  "items": [
    {
      "id": 123,
      "date": "2026-01-11",
      "stock_name": "科大讯飞",
      "concepts": [
        {"id": 1, "name": "人工智能"},
        {"id": 2, "name": "语音识别"}
      ],
      ...
    }
  ],
  ...
}
```

#### 4.3.2 涨停榜按概念板块筛选

```
GET /api/v1/zt-pool
Query Parameters:
  - concept_ids: string (逗号分隔，如 "1,2,3")
  - concept_names: string (逗号分隔，如 "人工智能,新能源")
  - date: string (日期)
  - ... 其他现有参数

Response: 扩展现有响应，包含 concepts 字段
{
  "items": [
    {
      "id": 456,
      "date": "2026-01-11",
      "stock_code": "002230",
      "stock_name": "科大讯飞",
      "concepts": [
        {"id": 1, "name": "人工智能"},
        {"id": 2, "name": "语音识别"}
      ],
      ...
    }
  ],
  ...
}
```

#### 4.3.3 个股资金流按概念板块筛选

```
GET /api/v1/stock-fund-flow
Query Parameters:
  - concept_ids: string (逗号分隔，如 "1,2,3")
  - concept_names: string (逗号分隔，如 "人工智能,新能源")
  - start_date: string
  - end_date: string
  - ... 其他现有参数

Response: 扩展现有响应，包含 concepts 字段
{
  "items": [
    {
      "id": 789,
      "date": "2026-01-11",
      "stock_code": "002230",
      "stock_name": "科大讯飞",
      "concepts": [
        {"id": 1, "name": "人工智能"},
        {"id": 2, "name": "语音识别"}
      ],
      ...
    }
  ],
  ...
}
```

### 4.4 股票概念关联管理 API

#### 4.4.1 为股票添加概念板块

```
POST /api/v1/stock-concepts/mapping
Request Body:
{
  "stock_name": "科大讯飞",
  "concept_ids": [1, 2, 3]
}

Response:
{
  "stock_name": "科大讯飞",
  "concepts": [
    {"id": 1, "name": "人工智能"},
    {"id": 2, "name": "语音识别"},
    {"id": 3, "name": "5G"}
  ]
}
```

#### 4.4.2 更新股票的概念板块

```
PUT /api/v1/stock-concepts/mapping/{stock_name}
Request Body:
{
  "concept_ids": [1, 2]  // 替换所有关联
}
```

#### 4.4.3 获取股票的概念板块

```
GET /api/v1/stock-concepts/mapping/{stock_name}
Response:
{
  "stock_name": "科大讯飞",
  "concepts": [
    {"id": 1, "name": "人工智能"},
    {"id": 2, "name": "语音识别"}
  ]
}
```

#### 4.4.4 批量查询股票概念板块

```
POST /api/v1/stock-concepts/mapping/batch
Request Body:
{
  "stock_names": ["科大讯飞", "比亚迪", "宁德时代"]
}

Response:
{
  "科大讯飞": [
    {"id": 1, "name": "人工智能"},
    {"id": 2, "name": "语音识别"}
  ],
  "比亚迪": [
    {"id": 3, "name": "新能源汽车"},
    {"id": 4, "name": "锂电池"}
  ],
  "宁德时代": [
    {"id": 4, "name": "锂电池"},
    {"id": 5, "name": "新能源"}
  ]
}
```

## 5. 前端界面设计

### 5.1 股票概念板块管理界面（新增）

创建独立的股票概念板块管理页面：

```vue
<!-- views/StockConcept/index.vue -->
<template>
  <div class="stock-concept">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>股票概念板块管理</span>
          <el-button type="primary" @click="handleAddConcept">
            <el-icon><Plus /></el-icon>
            新增概念板块
          </el-button>
        </div>
      </template>
      
      <!-- 搜索栏 -->
      <div class="filter-bar">
        <el-input
          v-model="searchStockName"
          placeholder="输入股票名称"
          clearable
          style="width: 200px"
          @clear="handleSearch"
        />
        <el-select
          v-model="selectedConceptIds"
          multiple
          filterable
          placeholder="选择概念板块"
          clearable
          style="width: 200px"
          @change="handleSearch"
        >
          <el-option
            v-for="concept in conceptOptions"
            :key="concept.id"
            :label="concept.name"
            :value="concept.id"
          />
        </el-select>
        <el-button type="primary" @click="handleSearch">查询</el-button>
      </div>
      
      <!-- 股票概念关联表格 -->
      <el-table :data="mappingData" border>
        <el-table-column prop="stock_name" label="股票名称" width="150" />
        <el-table-column label="概念板块" min-width="300">
          <template #default="{ row }">
            <el-tag
              v-for="concept in row.concepts"
              :key="concept.id"
              size="small"
              style="margin-right: 5px; margin-bottom: 2px"
            >
              {{ concept.name }}
            </el-tag>
            <el-button
              type="text"
              size="small"
              @click="handleEditMapping(row)"
            >
              <el-icon><Edit /></el-icon>
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="handleEditMapping(row)">
              编辑
            </el-button>
            <el-button type="danger" link size="small" @click="handleDeleteMapping(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 编辑股票概念关联对话框 -->
    <el-dialog
      v-model="mappingDialogVisible"
      :title="mappingDialogTitle"
      width="500px"
    >
      <el-form :model="mappingForm" label-width="100px">
        <el-form-item label="股票名称">
          <el-input
            v-model="mappingForm.stock_name"
            :disabled="!!mappingForm.id"
            placeholder="请输入股票名称"
          />
        </el-form-item>
        <el-form-item label="概念板块">
          <el-select
            v-model="mappingForm.concept_ids"
            multiple
            filterable
            placeholder="请选择概念板块（可多选）"
            style="width: 100%"
          >
            <el-option
              v-for="concept in conceptOptions"
              :key="concept.id"
              :label="concept.name"
              :value="concept.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="mappingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitMapping">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
```

### 5.2 交易日历表单扩展

在新增/编辑交易日历对话框中添加概念板块选择：

```vue
<el-form-item label="概念板块" prop="concepts">
  <el-select
    v-model="formData.concept_ids"
    multiple
    filterable
    placeholder="请选择概念板块（可多选）"
    style="width: 100%"
    @change="handleConceptChange"
  >
    <el-option
      v-for="concept in conceptOptions"
      :key="concept.id"
      :label="concept.name"
      :value="concept.id"
    />
  </el-select>
  <el-button
    type="text"
    size="small"
    @click="showConceptDialog = true"
    style="margin-top: 5px"
  >
    <el-icon><Plus /></el-icon>
    添加新概念板块
  </el-button>
</el-form-item>
```

### 5.2 交易日历表格扩展

在表格中显示概念板块标签：

```vue
<el-table-column label="概念板块" width="200">
  <template #default="{ row }">
    <el-tag
      v-for="concept in row.concepts"
      :key="concept.id"
      size="small"
      style="margin-right: 5px; margin-bottom: 2px"
    >
      {{ concept.name }}
    </el-tag>
    <span v-if="!row.concepts || row.concepts.length === 0" style="color: #999;">-</span>
  </template>
</el-table-column>
```

### 5.3 涨停榜表格扩展

在涨停榜表格中显示概念板块：

```vue
<el-table-column label="概念板块" width="200">
  <template #default="{ row }">
    <el-tag
      v-for="concept in row.concepts"
      :key="concept.id"
      size="small"
      type="warning"
      style="margin-right: 5px; margin-bottom: 2px"
    >
      {{ concept.name }}
    </el-tag>
    <span v-if="!row.concepts || row.concepts.length === 0" style="color: #999;">-</span>
  </template>
</el-table-column>
```

### 5.4 个股资金流表格扩展

在个股资金流表格中显示概念板块：

```vue
<el-table-column label="概念板块" width="200">
  <template #default="{ row }">
    <el-tag
      v-for="concept in row.concepts"
      :key="concept.id"
      size="small"
      type="info"
      style="margin-right: 5px; margin-bottom: 2px"
    >
      {{ concept.name }}
    </el-tag>
    <span v-if="!row.concepts || row.concepts.length === 0" style="color: #999;">-</span>
  </template>
</el-table-column>
```

### 5.5 筛选栏扩展（三个模块通用）

为三个模块的筛选栏都添加概念板块筛选：

```vue
<el-select
  v-model="conceptIds"
  multiple
  filterable
  placeholder="概念板块"
  clearable
  style="width: 200px"
  @change="handleSearch"
>
  <el-option
    v-for="concept in conceptOptions"
    :key="concept.id"
    :label="concept.name"
    :value="concept.id"
  />
</el-select>
```

### 5.4 概念板块管理对话框

```vue
<el-dialog
  v-model="conceptDialogVisible"
  title="概念板块管理"
  width="600px"
>
  <el-table :data="conceptList" border>
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="code" label="代码" />
    <el-table-column prop="description" label="描述" show-overflow-tooltip />
    <el-table-column label="操作" width="150">
      <template #default="{ row }">
        <el-button type="primary" link size="small" @click="handleEditConcept(row)">
          编辑
        </el-button>
        <el-button type="danger" link size="small" @click="handleDeleteConcept(row)">
          删除
        </el-button>
      </template>
    </el-table-column>
  </el-table>
  
  <template #footer>
    <el-button @click="conceptDialogVisible = false">关闭</el-button>
    <el-button type="primary" @click="handleAddConcept">新增概念板块</el-button>
  </template>
</el-dialog>
```

## 6. 实现步骤

### 阶段1：数据库和模型
1. 创建数据库迁移文件（Alembic）
   - 创建 `stock_concept` 表
   - 创建 `stock_concept_mapping` 表（核心关联表）
   - 可选：创建 `trading_calendar_concept` 表
2. 创建 `StockConcept` 模型
3. 创建 `StockConceptMapping` 模型
4. 扩展各模块模型，添加概念板块查询方法
   - `TradingCalendar`
   - `ZtPool`
   - `StockFundFlow`

### 阶段2：后端API
1. 创建概念板块服务 (`StockConceptService`)
   - CRUD 操作
   - 查询和筛选
2. 创建股票概念关联服务 (`StockConceptMappingService`)
   - 为股票添加/更新/删除概念板块
   - 批量查询股票概念板块
3. 创建概念板块API路由 (`/api/v1/stock-concepts`)
4. 创建股票概念关联API路由 (`/api/v1/stock-concepts/mapping`)
5. 扩展各模块服务，支持概念板块筛选和展示
   - `TradingCalendarService`：添加概念板块筛选和关联查询
   - `ZtPoolService`：添加概念板块筛选和关联查询
   - `StockFundFlowService`：添加概念板块筛选和关联查询
6. 扩展各模块API，支持概念板块参数
   - `/api/v1/trading-calendar`：添加 `concept_ids` 和 `concept_names` 参数
   - `/api/v1/zt-pool`：添加 `concept_ids` 和 `concept_names` 参数
   - `/api/v1/stock-fund-flow`：添加 `concept_ids` 和 `concept_names` 参数

### 阶段3：前端界面
1. 创建概念板块API客户端
2. 创建股票概念板块管理页面（新增）
   - 股票概念关联管理
   - 概念板块管理
3. 扩展交易日历界面
   - 表格显示概念板块标签
   - 添加概念板块筛选
4. 扩展涨停榜界面
   - 表格显示概念板块标签
   - 添加概念板块筛选
5. 扩展个股资金流界面
   - 表格显示概念板块标签
   - 添加概念板块筛选
6. 创建通用概念板块选择组件（可复用）

### 阶段4：测试和优化
1. 单元测试
2. 集成测试
3. 性能优化（索引、查询优化）
4. UI/UX 优化

## 7. 数据初始化

### 7.1 常见概念板块

建议预置以下常见概念板块：

```python
COMMON_CONCEPTS = [
    {"name": "人工智能", "code": "AI"},
    {"name": "新能源", "code": "NE"},
    {"name": "5G", "code": "5G"},
    {"name": "芯片", "code": "CHIP"},
    {"name": "新能源汽车", "code": "NEV"},
    {"name": "光伏", "code": "PV"},
    {"name": "锂电池", "code": "BATTERY"},
    {"name": "医药", "code": "MED"},
    {"name": "消费电子", "code": "CE"},
    {"name": "军工", "code": "DEFENSE"},
]
```

## 8. 注意事项

1. **数据一致性**：
   - 删除概念板块时，需要处理关联的所有记录（三个模块）
   - 股票名称变更时，需要更新 `stock_concept_mapping` 表
   
2. **性能优化**：
   - 大量数据时，考虑使用缓存（Redis）缓存概念板块列表
   - 查询时使用 `joinedload` 或 `selectinload` 优化关联查询
   - 考虑为常用查询创建数据库视图
   
3. **搜索优化**：
   - 概念板块名称支持模糊搜索，考虑添加全文搜索索引
   - 股票名称查询概念板块时，考虑添加缓存
   
4. **用户体验**：
   - 概念板块选择支持多选和搜索，提供快速添加新概念的入口
   - 在三个模块中统一概念板块的显示样式
   - 提供批量管理股票概念板块的功能
   
5. **数据导入**：
   - 考虑在导入交易日历数据时，自动识别并关联概念板块
   - 考虑从涨停榜的 `concept` 字段（Text）中提取并建立关联
   - 提供数据迁移脚本，将现有数据转换为关联表数据
   
6. **查询逻辑**：
   - 三个模块统一通过 `stock_concept_mapping` 表查询概念板块
   - 交易日历可以支持记录级别的概念板块覆盖（通过 `trading_calendar_concept` 表）
   - 查询时优先使用记录级别的关联，其次使用股票名称的通用关联
   
7. **兼容性**：
   - 涨停榜现有的 `concept` 字段（Text）可以保留用于兼容
   - 逐步迁移到关联表结构

## 9. 扩展功能（可选）

1. **概念板块统计**：
   - 统计每个概念板块在三个模块中的出现次数
   - 统计概念板块的交易次数、盈亏情况（交易日历）
   - 统计概念板块的涨停次数（涨停榜）
   - 统计概念板块的资金流向（个股资金流）
   
2. **概念板块趋势**：
   - 分析概念板块的热度趋势
   - 分析概念板块的资金流向趋势
   - 分析概念板块的涨停频率趋势
   
3. **智能推荐**：
   - 根据股票名称自动推荐可能的概念板块
   - 基于历史数据推荐概念板块
   - 基于行业信息推荐概念板块
   
4. **概念板块分组**：
   - 支持概念板块的分组管理（如：科技类、消费类等）
   - 支持概念板块的层级结构（如：新能源 > 新能源汽车 > 锂电池）
   
5. **数据同步**：
   - 从外部数据源（如 akshare）同步概念板块信息
   - 自动更新股票的概念板块关联
   
6. **概念板块分析**：
   - 概念板块关联度分析（哪些概念板块经常一起出现）
   - 概念板块轮动分析
   - 概念板块资金流向分析
