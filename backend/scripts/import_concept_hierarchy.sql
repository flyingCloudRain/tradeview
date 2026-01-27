-- 导入概念层级结构和个股关联的SQL脚本
-- 
-- 使用方法：
--   1. 修改下面的数据部分（INSERT语句）
--   2. 执行SQL脚本：psql -h host -U user -d database -f import_concept_hierarchy.sql
--   或者通过数据库客户端工具执行
--
-- 数据格式说明：
--   - 先插入概念（一级、二级、三级）
--   - 然后建立个股与概念的关联
--   - 最后更新stock_count统计字段

BEGIN;

-- ============================================
-- 第一部分：插入概念（如果不存在）
-- ============================================

-- 插入一级概念（如果不存在）
INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
SELECT 
    '商业航天'::VARCHAR(100),
    NULL,
    NULL,
    NULL,
    1,
    NULL,  -- path会在后面更新
    0,
    0,
    NOW(),
    NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM stock_concept WHERE name = '商业航天'
);

-- 获取一级概念ID（用于后续插入）
DO $$
DECLARE
    v_level1_id INTEGER;
    v_level2_id INTEGER;
    v_level3_id INTEGER;
BEGIN
    -- 获取一级概念ID
    SELECT id INTO v_level1_id FROM stock_concept WHERE name = '商业航天';
    
    -- 更新一级概念的path
    UPDATE stock_concept SET path = id::TEXT WHERE id = v_level1_id;
    
    -- 插入二级概念：卫星（如果不存在）
    INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
    SELECT 
        '卫星'::VARCHAR(100),
        NULL,
        NULL,
        v_level1_id,
        2,
        NULL,  -- path会在后面更新
        0,
        0,
        NOW(),
        NOW()
    WHERE NOT EXISTS (
        SELECT 1 FROM stock_concept WHERE name = '卫星' AND parent_id = v_level1_id
    )
    RETURNING id INTO v_level2_id;
    
    -- 如果已存在，获取ID
    IF v_level2_id IS NULL THEN
        SELECT id INTO v_level2_id FROM stock_concept WHERE name = '卫星' AND parent_id = v_level1_id;
    END IF;
    
    -- 更新二级概念的path
    UPDATE stock_concept SET path = (SELECT path FROM stock_concept WHERE id = v_level1_id) || '/' || v_level2_id::TEXT 
    WHERE id = v_level2_id;
    
    -- 插入三级概念：千帆星座（如果不存在）
    INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
    SELECT 
        '千帆星座'::VARCHAR(100),
        NULL,
        NULL,
        v_level2_id,
        3,
        NULL,  -- path会在后面更新
        0,
        0,
        NOW(),
        NOW()
    WHERE NOT EXISTS (
        SELECT 1 FROM stock_concept WHERE name = '千帆星座' AND parent_id = v_level2_id
    )
    RETURNING id INTO v_level3_id;
    
    -- 如果已存在，获取ID
    IF v_level3_id IS NULL THEN
        SELECT id INTO v_level3_id FROM stock_concept WHERE name = '千帆星座' AND parent_id = v_level2_id;
    END IF;
    
    -- 更新三级概念的path
    UPDATE stock_concept SET path = (SELECT path FROM stock_concept WHERE id = v_level2_id) || '/' || v_level3_id::TEXT 
    WHERE id = v_level3_id;
    
END $$;

-- ============================================
-- 第二部分：关联个股到概念
-- ============================================

-- 为"千帆星座"概念关联个股
DO $$
DECLARE
    v_concept_id INTEGER;
    v_stock_name VARCHAR(50);
    v_stock_names TEXT[] := ARRAY[
        '乾照光电',
        '东方明珠',
        '天银机电',
        '上海瀚讯',
        '航天智装',
        '立昂微',
        '陕西华达',
        '长江通信',
        '北摩高科',
        '隆盛科技',
        '鸿远电子'
    ];
BEGIN
    -- 获取"千帆星座"概念的ID
    SELECT id INTO v_concept_id 
    FROM stock_concept 
    WHERE name = '千帆星座' 
    AND level = 3;
    
    IF v_concept_id IS NULL THEN
        RAISE EXCEPTION '未找到"千帆星座"概念';
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
-- 第三部分：更新stock_count统计字段
-- ============================================

UPDATE stock_concept sc
SET stock_count = (
    SELECT COUNT(*) 
    FROM stock_concept_mapping scm 
    WHERE scm.concept_id = sc.id
);

COMMIT;

-- ============================================
-- 验证查询
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
WHERE sc1.name = '商业航天'
GROUP BY sc1.name, sc2.name, sc3.name
ORDER BY sc2.name, sc3.name;
