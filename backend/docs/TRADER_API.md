# 游资管理API文档

## 概述

游资管理API提供了完整的游资（Trader）和机构关联（TraderBranch）的CRUD操作功能。

## API端点

### 1. 获取游资列表

**GET** `/api/v1/lhb/traders`

获取所有游资及其关联机构列表。

**响应示例：**
```json
[
  {
    "id": 1,
    "name": "龙飞虎",
    "aka": "龙飞虎(克拉美书)股灾期间曾为桃县精神领袖...",
    "branches": [
      {
        "id": 1,
        "trader_id": 1,
        "institution_name": "华泰证券股份有限公司南京六合雄州西路证券营业部",
        "institution_code": null
      }
    ]
  }
]
```

### 2. 获取游资详情

**GET** `/api/v1/lhb/traders/{trader_id}`

根据ID获取游资详情。

**路径参数：**
- `trader_id` (int): 游资ID

**响应示例：**
```json
{
  "id": 1,
  "name": "龙飞虎",
  "aka": "龙飞虎(克拉美书)股灾期间曾为桃县精神领袖...",
  "branches": [...]
}
```

### 3. 创建游资

**POST** `/api/v1/lhb/traders`

创建新的游资。

**请求体：**
```json
{
  "name": "新游资名称",
  "aka": "游资说明（可选）",
  "branches": ["机构名称1", "机构名称2"]
}
```

**响应：** 201 Created，返回创建的游资对象

**错误响应：**
- `400 Bad Request`: 游资名称已存在
- `500 Internal Server Error`: 服务器错误

### 4. 更新游资

**PUT** `/api/v1/lhb/traders/{trader_id}`

更新游资信息。

**路径参数：**
- `trader_id` (int): 游资ID

**请求体：**
```json
{
  "name": "更新后的名称（可选）",
  "aka": "更新后的说明（可选）"
}
```

**响应：** 返回更新后的游资对象

**错误响应：**
- `400 Bad Request`: 游资名称已存在
- `404 Not Found`: 游资不存在
- `500 Internal Server Error`: 服务器错误

### 5. 删除游资

**DELETE** `/api/v1/lhb/traders/{trader_id}`

删除游资（级联删除所有关联的机构）。

**路径参数：**
- `trader_id` (int): 游资ID

**响应：** 204 No Content

**错误响应：**
- `404 Not Found`: 游资不存在

### 6. 添加机构关联

**POST** `/api/v1/lhb/traders/{trader_id}/branches`

为游资添加机构关联。

**路径参数：**
- `trader_id` (int): 游资ID

**请求体：**
```json
{
  "institution_name": "机构名称",
  "institution_code": "机构代码（可选）"
}
```

**响应：** 201 Created，返回创建的机构关联对象

**错误响应：**
- `404 Not Found`: 游资不存在

### 7. 更新机构关联

**PUT** `/api/v1/lhb/traders/{trader_id}/branches/{branch_id}`

更新游资的机构关联。

**路径参数：**
- `trader_id` (int): 游资ID
- `branch_id` (int): 机构关联ID

**请求体：**
```json
{
  "institution_name": "更新后的机构名称（可选）",
  "institution_code": "更新后的机构代码（可选）"
}
```

**响应：** 返回更新后的机构关联对象

**错误响应：**
- `400 Bad Request`: 机构名称已存在或不属于指定游资
- `404 Not Found`: 机构关联不存在
- `500 Internal Server Error`: 服务器错误

### 8. 删除机构关联

**DELETE** `/api/v1/lhb/traders/{trader_id}/branches/{branch_id}`

删除游资的机构关联。

**路径参数：**
- `trader_id` (int): 游资ID
- `branch_id` (int): 机构关联ID

**响应：** 204 No Content

**错误响应：**
- `404 Not Found`: 机构关联不存在或不属于指定游资

### 9. 通过机构查找游资

**GET** `/api/v1/lhb/traders/lookup`

通过营业部代码或名称反查游资。

**查询参数：**
- `institution_code` (string, 可选): 营业部代码
- `institution_name` (string, 可选): 营业部名称

**响应：** 返回匹配的游资对象，如果没有找到则返回null

## 数据模型

### TraderResponse
```json
{
  "id": 1,
  "name": "游资名称",
  "aka": "游资说明",
  "branches": [TraderBranchResponse]
}
```

### TraderBranchResponse
```json
{
  "id": 1,
  "trader_id": 1,
  "institution_name": "机构名称",
  "institution_code": "机构代码（可选）"
}
```

### TraderCreateRequest
```json
{
  "name": "游资名称（必填，1-200字符）",
  "aka": "游资说明（可选，最多1000字符）",
  "branches": ["机构名称1", "机构名称2"]  // 可选
}
```

### TraderUpdateRequest
```json
{
  "name": "游资名称（可选，1-200字符）",
  "aka": "游资说明（可选，最多1000字符）"
}
```

### TraderBranchCreateRequest
```json
{
  "institution_name": "机构名称（必填，1-200字符）",
  "institution_code": "机构代码（可选，最多50字符）"
}
```

## 使用示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/lhb"

# 1. 创建游资
response = requests.post(f"{BASE_URL}/traders", json={
    "name": "新游资",
    "aka": "游资说明",
    "branches": ["机构1", "机构2"]
})
trader = response.json()
trader_id = trader["id"]

# 2. 更新游资
requests.put(f"{BASE_URL}/traders/{trader_id}", json={
    "aka": "更新后的说明"
})

# 3. 添加机构
requests.post(f"{BASE_URL}/traders/{trader_id}/branches", json={
    "institution_name": "新机构",
    "institution_code": "CODE001"
})

# 4. 获取游资列表
traders = requests.get(f"{BASE_URL}/traders").json()

# 5. 删除游资
requests.delete(f"{BASE_URL}/traders/{trader_id}")
```

### cURL示例

```bash
# 创建游资
curl -X POST "http://localhost:8000/api/v1/lhb/traders" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新游资",
    "aka": "游资说明",
    "branches": ["机构1", "机构2"]
  }'

# 更新游资
curl -X PUT "http://localhost:8000/api/v1/lhb/traders/1" \
  -H "Content-Type: application/json" \
  -d '{
    "aka": "更新后的说明"
  }'

# 删除游资
curl -X DELETE "http://localhost:8000/api/v1/lhb/traders/1"
```

## 注意事项

1. **唯一性约束**：
   - 游资名称必须唯一
   - 同一游资的机构名称必须唯一

2. **级联删除**：
   - 删除游资时会自动删除所有关联的机构（TraderBranch）
   - 删除机构不会影响游资本身

3. **数据验证**：
   - 游资名称：1-200字符
   - 游资说明：最多1000字符
   - 机构名称：1-200字符
   - 机构代码：最多50字符

4. **错误处理**：
   - 所有API都包含适当的错误处理和HTTP状态码
   - 详细的错误信息会在响应中返回

## 测试

运行测试脚本验证功能：

```bash
PYTHONPATH=. python backend/scripts/test_trader_crud.py
```
