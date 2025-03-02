-- Stocks reference table
CREATE TABLE stock_data.stocks (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap BIGINT,
    exchange VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_ticker UNIQUE (ticker)
);

-- Create index on ticker for quick lookups
CREATE INDEX idx_stocks_ticker ON stock_data.stocks(ticker);
CREATE INDEX idx_stocks_sector ON stock_data.stocks(sector);
CREATE INDEX idx_stocks_industry ON stock_data.stocks(industry);

-- TimescaleDB hypertable for price data (to be created in TimescaleDB instance)
CREATE TABLE stock_data.price_data (
    id BIGSERIAL,
    stock_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open NUMERIC(19,6),
    high NUMERIC(19,6),
    low NUMERIC(19,6),
    close NUMERIC(19,6),
    volume BIGINT,
    adjusted_close NUMERIC(19,6),
    data_source VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_stock FOREIGN KEY (stock_id) REFERENCES stock_data.stocks(id) ON DELETE CASCADE
);

-- Add primary key constraint
ALTER TABLE stock_data.price_data ADD PRIMARY KEY (id, timestamp);

-- Create hypertable (this will be executed on TimescaleDB instance)
-- SELECT create_hypertable('stock_data.price_data', 'timestamp');

-- Create indexes for price data
CREATE INDEX idx_price_data_stock_id_timestamp ON stock_data.price_data(stock_id, timestamp DESC);

-- Data sources table
CREATE TABLE stock_data.data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    config JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_data_source_name UNIQUE (name)
);

-- Table for storing feature data
CREATE TABLE stock_data.feature_data (
    id BIGSERIAL,
    stock_id INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value NUMERIC(19,6),
    window_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_stock FOREIGN KEY (stock_id) REFERENCES stock_data.stocks(id) ON DELETE CASCADE
);

-- Add primary key constraint
ALTER TABLE stock_data.feature_data ADD PRIMARY KEY (id, timestamp);

-- Create hypertable (this will be executed on TimescaleDB instance)
-- SELECT create_hypertable('stock_data.feature_data', 'timestamp');

-- Create indexes for feature data
CREATE INDEX idx_feature_data_stock_id_feature ON stock_data.feature_data(stock_id, feature_name, timestamp DESC);