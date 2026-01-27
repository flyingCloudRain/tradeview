# 概念层级结构和个股关联导入指南

## SQL导入方式

### 1. 使用示例SQL脚本

已提供示例SQL脚本：`import_commercial_aerospace_example.sql`

```bash
# 通过psql执行
psql -h <host> -U <user> -d <database> -f scripts/import_commercial_aerospace_example.sql

# 或者通过数据库客户端工具执行
```

### 2. 使用SQL模板

使用 `import_concept_hierarchy_template.sql` 作为模板，修改其中的：
- 概念名称（一级、二级、三级）
- 个股列表

### 3. SQL脚本结构

每个SQL脚本包含以下部分：

#### 步骤1：插入概念层级结构
```sql
-- 插入一级概念
INSERT INTO stock_concept (name, level, ...) VALUES (...);

-- 插入二级概念（使用DO块动态获取父概念ID）
DO $$ ... END $$;

-- 插入三级概念（使用DO块动态获取父概念ID）
DO $$ ... END $$;
```

#### 步骤2：关联个股到概念
```sql
DO $$
DECLARE
    v_concept_id INTEGER;
    v_stock_names TEXT[] := ARRAY['个股1', '个股2', ...];
BEGIN
    -- 获取概念ID
    -- 批量插入关联
END $$;
```

#### 步骤3：更新统计字段
```sql
UPDATE stock_concept SET stock_count = (SELECT COUNT(*) FROM stock_concept_mapping WHERE concept_id = stock_concept.id);
```

#### 步骤4：验证查询
```sql
SELECT ... -- 查询导入结果
```

## 数据格式

### 表格格式示例

| 一级概念 | 二级概念 | 三级概念 | 个股列表 |
|---------|---------|---------|---------|
| 商业航天 | 卫星 | 千帆星座 | 乾照光电, 东方明珠, 天银机电, ... |

### SQL数组格式

```sql
v_stock_names TEXT[] := ARRAY[
    '乾照光电',
    '东方明珠',
    '天银机电',
    -- 更多个股...
];
```

## 注意事项

1. **幂等性**：所有INSERT语句都使用 `WHERE NOT EXISTS` 确保不会重复插入
2. **事务**：整个脚本包裹在 `BEGIN ... COMMIT` 中，确保原子性
3. **Path字段**：自动计算层级路径（如：`1/5/12`）
4. **Stock_count**：自动更新统计字段

## 快速导入示例

### 示例1：商业航天 -> 卫星 -> 千帆星座

```sql
-- 直接执行示例脚本
\i scripts/import_commercial_aerospace_example.sql
```

### 示例2：自定义导入

1. 复制模板文件
2. 修改概念名称和个股列表
3. 执行SQL脚本

## 验证导入结果

执行验证查询：

```sql
SELECT 
    sc1.name AS "一级概念",
    sc2.name AS "二级概念",
    sc3.name AS "三级概念",
    COUNT(DISTINCT scm.stock_name) AS "关联个股数",
    STRING_AGG(DISTINCT scm.stock_name, ', ' ORDER BY scm.stock_name) AS "个股列表"
FROM stock_concept sc1
LEFT JOIN stock_concept sc2 ON sc2.parent_id = sc1.id
LEFT JOIN stock_concept sc3 ON sc3.parent_id = sc2.id
LEFT JOIN stock_concept_mapping scm ON scm.concept_id = COALESCE(sc3.id, sc2.id, sc1.id)
WHERE sc1.name = '商业航天'
GROUP BY sc1.name, sc2.name, sc3.name
ORDER BY sc2.name, sc3.name;
```

## 常见问题

### Q: 如果概念已存在怎么办？
A: SQL脚本使用 `WHERE NOT EXISTS` 检查，已存在的概念不会重复插入。

### Q: 如果个股关联已存在怎么办？
A: 使用 `WHERE NOT EXISTS` 检查，已存在的关联不会重复插入。

### Q: 如何批量导入多个概念层级？
A: 可以复制多个DO块，或者将多个概念的数据合并到一个脚本中。

### Q: 如何导入只有二级概念的情况？
A: 跳过三级概念的插入部分，直接将个股关联到二级概念。
