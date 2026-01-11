-- 交易复盘系统数据库表结构
-- 适用于PostgreSQL/Supabase

-- 1. 龙虎榜详情表
CREATE TABLE IF NOT EXISTS lhb_detail (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    close_price DECIMAL(10, 2),
    change_percent DECIMAL(5, 2),
    net_buy_amount DECIMAL(15, 2),
    buy_amount DECIMAL(15, 2),
    sell_amount DECIMAL(15, 2),
    total_amount DECIMAL(15, 2),
    turnover_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, stock_code)
);

CREATE INDEX IF NOT EXISTS idx_lhb_date ON lhb_detail(date);
CREATE INDEX IF NOT EXISTS idx_lhb_stock_code ON lhb_detail(stock_code);

COMMENT ON TABLE lhb_detail IS '龙虎榜详情表';

-- 2. 龙虎榜机构明细表
CREATE TABLE IF NOT EXISTS lhb_institution (
    id SERIAL PRIMARY KEY,
    lhb_detail_id INTEGER REFERENCES lhb_detail(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    institution_name VARCHAR(100),
    buy_amount DECIMAL(15, 2),
    sell_amount DECIMAL(15, 2),
    net_buy_amount DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_lhb_institution_date ON lhb_institution(date);
CREATE INDEX IF NOT EXISTS idx_lhb_institution_stock ON lhb_institution(stock_code);

COMMENT ON TABLE lhb_institution IS '龙虎榜机构明细表';

-- 3. 活跃机构详情表
CREATE TABLE IF NOT EXISTS capital_detail (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    capital_name VARCHAR(100) NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    buy_amount DECIMAL(15, 2),
    sell_amount DECIMAL(15, 2),
    net_buy_amount DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, capital_name, stock_code)
);

CREATE INDEX IF NOT EXISTS idx_capital_date ON capital_detail(date);
CREATE INDEX IF NOT EXISTS idx_capital_name ON capital_detail(capital_name);
CREATE INDEX IF NOT EXISTS idx_capital_stock ON capital_detail(stock_code);

COMMENT ON TABLE capital_detail IS '活跃机构详情表';

-- 4. 大盘指数历史表
CREATE TABLE IF NOT EXISTS index_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    index_code VARCHAR(20) NOT NULL,
    index_name VARCHAR(50) NOT NULL,
    close_price DECIMAL(10, 2),
    change_percent DECIMAL(5, 2),
    volume BIGINT,
    amount DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, index_code)
);

CREATE INDEX IF NOT EXISTS idx_index_date ON index_history(date);
CREATE INDEX IF NOT EXISTS idx_index_code ON index_history(index_code);

COMMENT ON TABLE index_history IS '大盘指数历史表';

-- 5. 概念板块历史表
CREATE TABLE IF NOT EXISTS sector_history (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    sector_code VARCHAR(20) NOT NULL,
    sector_name VARCHAR(50) NOT NULL,
    change_percent DECIMAL(5, 2),
    rise_count INTEGER,
    fall_count INTEGER,
    total_count INTEGER,
    total_amount DECIMAL(15, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, sector_code)
);

CREATE INDEX IF NOT EXISTS idx_sector_date ON sector_history(date);
CREATE INDEX IF NOT EXISTS idx_sector_code ON sector_history(sector_code);

COMMENT ON TABLE sector_history IS '概念板块历史表';

-- 6. 个股资金流表
CREATE TABLE IF NOT EXISTS stock_fund_flow (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    main_inflow DECIMAL(15, 2),
    main_outflow DECIMAL(15, 2),
    main_net_inflow DECIMAL(15, 2),
    turnover_rate DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, stock_code)
);

CREATE INDEX IF NOT EXISTS idx_fund_flow_date ON stock_fund_flow(date);
CREATE INDEX IF NOT EXISTS idx_fund_flow_stock ON stock_fund_flow(stock_code);

COMMENT ON TABLE stock_fund_flow IS '个股资金流表';

-- 7. 涨停池表
CREATE TABLE IF NOT EXISTS zt_pool (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    stock_code VARCHAR(10) NOT NULL,
    stock_name VARCHAR(50) NOT NULL,
    change_percent DECIMAL(5, 2),
    latest_price DECIMAL(10, 2),
    turnover_amount BIGINT,
    circulation_market_value DECIMAL(15, 2),
    total_market_value DECIMAL(15, 2),
    turnover_rate DECIMAL(5, 2),
    limit_up_capital BIGINT,
    first_limit_time TIME,
    last_limit_time TIME,
    explosion_count INTEGER DEFAULT 0,
    limit_up_statistics TEXT,
    consecutive_limit_count INTEGER,
    industry VARCHAR(100),
    concept TEXT,
    limit_up_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, stock_code)
);

CREATE INDEX IF NOT EXISTS idx_zt_pool_date ON zt_pool(date);
CREATE INDEX IF NOT EXISTS idx_zt_pool_stock ON zt_pool(stock_code);
CREATE INDEX IF NOT EXISTS idx_zt_pool_industry ON zt_pool(industry);
CREATE INDEX IF NOT EXISTS idx_zt_pool_consecutive ON zt_pool(consecutive_limit_count);

-- 为概念字段创建全文搜索索引（PostgreSQL）
CREATE INDEX IF NOT EXISTS idx_zt_pool_concept_gin ON zt_pool USING GIN(to_tsvector('simple', COALESCE(concept, '')));

COMMENT ON TABLE zt_pool IS '涨停池表';

