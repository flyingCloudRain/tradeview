-- 查询trader_branch表数据的SQL脚本
-- 可以直接在数据库中执行这些SQL语句来验证数据

-- 1. 查询总记录数
SELECT COUNT(*) as total_branches FROM trader_branch;

-- 2. 查询前20条记录
SELECT 
    tb.id,
    tb.trader_id,
    t.name as trader_name,
    tb.institution_name,
    tb.institution_code,
    tb.created_at
FROM trader_branch tb
LEFT JOIN trader t ON tb.trader_id = t.id
ORDER BY tb.id
LIMIT 20;

-- 3. 统计每个trader的branch数量
SELECT 
    t.id,
    t.name as trader_name,
    COUNT(tb.id) as branch_count
FROM trader t
LEFT JOIN trader_branch tb ON t.id = tb.trader_id
GROUP BY t.id, t.name
ORDER BY branch_count DESC
LIMIT 20;

-- 4. 检查没有branch的trader
SELECT 
    t.id,
    t.name as trader_name
FROM trader t
LEFT JOIN trader_branch tb ON t.id = tb.trader_id
WHERE tb.id IS NULL;

-- 5. 检查重复的(trader_id, institution_name)组合
SELECT 
    trader_id,
    institution_name,
    COUNT(*) as cnt
FROM trader_branch
GROUP BY trader_id, institution_name
HAVING COUNT(*) > 1;

-- 6. 检查孤立branch（trader_id不存在）
SELECT 
    tb.id,
    tb.trader_id,
    tb.institution_name
FROM trader_branch tb
LEFT JOIN trader t ON tb.trader_id = t.id
WHERE t.id IS NULL;

-- 7. 统计有代码和无代码的branch数量
SELECT 
    CASE 
        WHEN institution_code IS NULL OR institution_code = '' THEN '无代码'
        ELSE '有代码'
    END as code_status,
    COUNT(*) as count
FROM trader_branch
GROUP BY code_status;
