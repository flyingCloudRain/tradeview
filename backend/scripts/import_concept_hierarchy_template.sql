-- ============================================
-- 概念层级结构和个股关联导入SQL模板
-- ============================================
-- 
-- 使用说明：
--   1. 复制此模板文件
--   2. 修改下面的数据部分（概念名称和个股列表）
--   3. 执行SQL脚本
--
-- 数据格式：
--   一级概念 -> 二级概念 -> 三级概念 -> 个股列表
--   如果某个层级为空，可以跳过
-- ============================================

BEGIN;

-- ============================================
-- 步骤1：插入概念层级结构
-- ============================================

-- 1.1 插入一级概念（修改这里的名称）
INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
SELECT 
    '一级概念名称'::VARCHAR(100),  -- 修改这里
    NULL,
    NULL,
    NULL,
    1,
    NULL,
    0,
    0,
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM stock_concept WHERE name = '一级概念名称');

-- 1.2 插入二级概念（修改这里的名称和父概念）
DO $$
DECLARE
    v_level1_id INTEGER;
    v_level2_id INTEGER;
BEGIN
    SELECT id INTO v_level1_id FROM stock_concept WHERE name = '一级概念名称';  -- 修改这里
    
    INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
    SELECT 
        '二级概念名称'::VARCHAR(100),  -- 修改这里
        NULL,
        NULL,
        v_level1_id,
        2,
        NULL,
        0,
        0,
        NOW(),
        NOW()
    WHERE NOT EXISTS (SELECT 1 FROM stock_concept WHERE name = '二级概念名称' AND parent_id = v_level1_id)
    RETURNING id INTO v_level2_id;
    
    IF v_level2_id IS NULL THEN
        SELECT id INTO v_level2_id FROM stock_concept WHERE name = '二级概念名称' AND parent_id = v_level1_id;
    END IF;
    
    -- 更新path
    UPDATE stock_concept SET path = (SELECT path FROM stock_concept WHERE id = v_level1_id) || '/' || v_level2_id::TEXT 
    WHERE id = v_level2_id;
END $$;

-- 1.3 插入三级概念（修改这里的名称和父概念）
DO $$
DECLARE
    v_level2_id INTEGER;
    v_level3_id INTEGER;
BEGIN
    SELECT id INTO v_level2_id FROM stock_concept WHERE name = '二级概念名称';  -- 修改这里
    
    INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
    SELECT 
        '三级概念名称'::VARCHAR(100),  -- 修改这里（如果不需要三级概念，可以删除这部分）
        NULL,
        NULL,
        v_level2_id,
        3,
        NULL,
        0,
        0,
        NOW(),
        NOW()
    WHERE NOT EXISTS (SELECT 1 FROM stock_concept WHERE name = '三级概念名称' AND parent_id = v_level2_id)
    RETURNING id INTO v_level3_id;
    
    IF v_level3_id IS NULL THEN
        SELECT id INTO v_level3_id FROM stock_concept WHERE name = '三级概念名称' AND parent_id = v_level2_id;
    END IF;
    
    -- 更新path
    UPDATE stock_concept SET path = (SELECT path FROM stock_concept WHERE id = v_level2_id) || '/' || v_level3_id::TEXT 
    WHERE id = v_level3_id;
END $$;

-- ============================================
-- 步骤2：关联个股到概念
-- ============================================

-- 2.1 关联个股到三级概念（如果有三级概念）
-- 如果只有二级概念，将下面的 v_level3_id 改为 v_level2_id
DO $$
DECLARE
    v_concept_id INTEGER;
    v_stock_names TEXT[] := ARRAY[
        '个股1',      -- 修改这里：添加个股名称
        '个股2',
        '个股3'
        -- 继续添加更多个股...
    ];
    v_stock_name VARCHAR(50);
BEGIN
    -- 获取目标概念的ID（三级概念或二级概念）
    SELECT id INTO v_concept_id 
    FROM stock_concept 
    WHERE name = '三级概念名称'  -- 修改这里：改为对应的概念名称
    AND level = 3;  -- 如果是二级概念，改为 level = 2
    
    IF v_concept_id IS NULL THEN
        RAISE EXCEPTION '未找到目标概念';
    END IF;
    
    -- 批量插入个股关联（忽略已存在的）
    FOREACH v_stock_name IN ARRAY v_stock_names
    LOOP
        INSERT INTO stock_concept_mapping (stock_name, concept_id, created_at, updated_at)
        SELECT 
            v_stock_name::VARCHAR(50),
            v_concept_id,
            NOW(),
            NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM stock_concept_mapping 
            WHERE stock_name = v_stock_name 
            AND concept_id = v_concept_id
        );
    END LOOP;
END $$;

-- ============================================
-- 步骤3：更新stock_count统计字段
-- ============================================

UPDATE stock_concept sc
SET stock_count = (
    SELECT COUNT(*) 
    FROM stock_concept_mapping scm 
    WHERE scm.concept_id = sc.id
);

COMMIT;

-- ============================================
-- 步骤4：验证查询（可选）
-- ============================================

-- 查询导入结果
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
WHERE sc1.name = '一级概念名称'  -- 修改这里：改为你的一级概念名称
GROUP BY sc1.name, sc2.name, sc3.name
ORDER BY sc2.name, sc3.name;
