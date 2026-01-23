-- Algorithm configurations
CREATE TABLE algorithms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    strategy_type TEXT NOT NULL,
    config JSON NOT NULL,
    symbols JSON NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Trade execution log
CREATE TABLE trades (
    id TEXT PRIMARY KEY,
    algorithm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL,
    order_type TEXT NOT NULL,
    status TEXT NOT NULL,
    alpaca_order_id TEXT,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    filled_at TEXT,
    notes TEXT,
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id)
);

-- Portfolio snapshots for each algorithm (hourly + after trades)
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    algorithm_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    equity REAL NOT NULL,
    cash REAL NOT NULL,
    buying_power REAL,
    daily_pnl REAL,
    total_pnl REAL,
    positions JSON,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id)
);

-- Current positions per algorithm
CREATE TABLE positions (
    id TEXT PRIMARY KEY,
    algorithm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    quantity REAL NOT NULL,
    avg_entry_price REAL NOT NULL,
    current_price REAL,
    market_value REAL,
    unrealized_pnl REAL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id),
    UNIQUE(algorithm_id, symbol)
);

-- System state / metadata
CREATE TABLE system_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_trades_algorithm ON trades(algorithm_id);
CREATE INDEX idx_trades_submitted ON trades(submitted_at);
CREATE INDEX idx_snapshots_algorithm_timestamp ON snapshots(algorithm_id, created_at);
CREATE INDEX idx_positions_algorithm ON positions(algorithm_id);
