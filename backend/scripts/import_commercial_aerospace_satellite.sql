-- ============================================
-- 导入：商业航天 -> 卫星 -> 千帆星座 -> 个股
-- ============================================
-- 
-- 数据来源：
--   商业航天	卫星	千帆星座	乾照光电、东方明珠、天银机电、上海瀚讯、航天智装、立昂微、陕西华达、长江通信、北摩高科、隆盛科技、鸿远电子
-- ============================================

BEGIN;

-- ============================================
-- 步骤1：插入概念层级结构
-- ============================================

-- 1.1 插入一级概念：商业航天
INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
SELECT 
    '商业航天'::VARCHAR(100),
    NULL,
    NULL,
    NULL,
    1,
    NULL,
    0,
    0,
    NOW(),
    NOW()
WHERE NOT EXISTS (SELECT 1 FROM stock_concept WHERE name = '商业航天');

-- 更新一级概念的path
UPDATE stock_concept SET path = id::TEXT WHERE name = '商业航天' AND path IS NULL;

-- 1.2 插入二级概念：卫星
DO $$
DECLARE
    v_level1_id INTEGER;
    v_level2_id INTEGER;
BEGIN
    SELECT id INTO v_level1_id FROM stock_concept WHERE name = '商业航天';
    
    IF v_level1_id IS NULL THEN
        RAISE EXCEPTION '未找到"商业航天"概念';
    END IF;
    
    INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
    SELECT 
        '卫星'::VARCHAR(100),
        NULL,
        NULL,
        v_level1_id,
        2,
        NULL,
        0,
        0,
        NOW(),
        NOW()
    WHERE NOT EXISTS (SELECT 1 FROM stock_concept WHERE name = '卫星' AND parent_id = v_level1_id)
    RETURNING id INTO v_level2_id;
    
    IF v_level2_id IS NULL THEN
        SELECT id INTO v_level2_id FROM stock_concept WHERE name = '卫星' AND parent_id = v_level1_id;
    END IF;
    
    -- 更新二级概念的path
    UPDATE stock_concept SET path = (SELECT path FROM stock_concept WHERE id = v_level1_id) || '/' || v_level2_id::TEXT 
    WHERE id = v_level2_id AND path IS NULL;
END $$;

-- 1.3 插入三级概念：千帆星座
DO $$
DECLARE
    v_level2_id INTEGER;
    v_level3_id INTEGER;
BEGIN
    SELECT id INTO v_level2_id FROM stock_concept WHERE name = '卫星';
    
    IF v_level2_id IS NULL THEN
        RAISE EXCEPTION '未找到"卫星"概念';
    END IF;
    
    INSERT INTO stock_concept (name, code, description, parent_id, level, path, sort_order, stock_count, created_at, updated_at)
    SELECT 
        '千帆星座'::VARCHAR(100),
        NULL,
        NULL,
        v_level2_id,
        3,
        NULL,
        0,
        0,
        NOW(),
        NOW()
    WHERE NOT EXISTS (SELECT 1 FROM stock_concept WHERE name = '千帆星座' AND parent_id = v_level2_id)
    RETURNING id INTO v_level3_id;
    
    IF v_level3_id IS NULL THEN
        SELECT id INTO v_level3_id FROM stock_concept WHERE name = '千帆星座' AND parent_id = v_level2_id;
    END IF;
    
    -- 更新三级概念的path
    UPDATE stock_concept SET path = (SELECT path FROM stock_concept WHERE id = v_level2_id) || '/' || v_level3_id::TEXT 
    WHERE id = v_level3_id AND path IS NULL;
END $$;

-- ============================================
-- 步骤2：关联个股到"千帆星座"概念
-- ============================================

DO $$
DECLARE
    v_concept_id INTEGER;
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
    v_stock_name VARCHAR(50);
    v_inserted_count INTEGER := 0;
    v_existing_count INTEGER := 0;
BEGIN
    -- 获取"千帆星座"概念的ID
    SELECT id INTO v_concept_id 
    FROM stock_concept 
    WHERE name = '千帆星座' 
    AND level = 3;
    
    IF v_concept_id IS NULL THEN
        RAISE EXCEPTION '未找到"千帆星座"概念，请先执行概念插入部分';
    END IF;
    
    RAISE NOTICE '开始关联个股到概念: 千帆星座 (ID: %)', v_concept_id;
    
    -- 批量插入个股关联（忽略已存在的）
    FOREACH v_stock_name IN ARRAY v_stock_names
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM stock_concept_mapping 
            WHERE stock_name = v_stock_name 
            AND concept_id = v_concept_id
        ) THEN
            INSERT INTO stock_concept_mapping (stock_name, concept_id, created_at, updated_at)
            VALUES (v_stock_name::VARCHAR(50), v_concept_id, NOW(), NOW());
            v_inserted_count := v_inserted_count + 1;
            RAISE NOTICE '  ✓ 新增关联: %', v_stock_name;
        ELSE
            v_existing_count := v_existing_count + 1;
            RAISE NOTICE '  - 已存在: %', v_stock_name;
        END IF;
    END LOOP;
    
    RAISE NOTICE '个股关联完成: 新增 % 个, 已存在 % 个, 总计 % 个', 
        v_inserted_count, v_existing_count, array_length(v_stock_names, 1);
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
-- 步骤4：验证查询
-- ============================================

SELECT 
    sc1.name AS "一级概念",
    sc2.name AS "二级概念",
    sc3.name AS "三级概念",
    sc3.stock_count AS "关联个股数",
    STRING_AGG(DISTINCT scm.stock_name, '、' ORDER BY scm.stock_name) AS "个股列表"
FROM stock_concept sc1
LEFT JOIN stock_concept sc2 ON sc2.parent_id = sc1.id
LEFT JOIN stock_concept sc3 ON sc3.parent_id = sc2.id
LEFT JOIN stock_concept_mapping scm ON scm.concept_id = sc3.id
WHERE sc1.name = '商业航天'
  AND sc3.name = '千帆星座'
GROUP BY sc1.name, sc2.name, sc3.name, sc3.stock_count
ORDER BY sc2.name, sc3.name;
