# Paper Trading Algorithm Comparison Platform

## Technical Specification

### Overview

Build a serverless paper trading platform on Cloudflare that allows users to define, run, and compare multiple trading algorithms against Alpaca's paper trading API. The system should track performance metrics and provide a dashboard for comparison.

---

## Architecture

### Platform: Cloudflare Workers (Python via Pyodide)

**Why this stack:**
- Zero infrastructure management
- Python support via Pyodide (httpx, FastAPI, pandas available)
- Cron triggers for scheduled execution (free tier includes this)
- D1 (SQLite) for persistent storage
- Pages for static frontend hosting
- All within free tier for small-scale usage

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Cloudflare Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐    ┌─────────────────────┐        │
│  │  trading-engine     │    │  dashboard-api      │        │
│  │  (Python Worker)    │    │  (Python Worker)    │        │
│  │                     │    │                     │        │
│  │  - Cron: */1 * * * *│    │  - FastAPI routes   │        │
│  │  - Runs algorithms  │    │  - REST endpoints   │        │
│  │  - Executes trades  │    │  - Query D1         │        │
│  └──────────┬──────────┘    └──────────┬──────────┘        │
│             │                          │                    │
│             ▼                          ▼                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │                 D1 Database                      │       │
│  │  - algorithms, trades, snapshots, positions     │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │              Pages (Static Frontend)             │       │
│  │  - Dashboard UI (vanilla JS or React)           │       │
│  └─────────────────────────────────────────────────┘       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                 ┌─────────────────────────┐
                 │   Alpaca Paper API      │
                 │   paper-api.alpaca.     │
                 │   markets               │
                 └─────────────────────────┘
```

---

## External Dependencies

### Alpaca Paper Trading API

**Base URL:** `https://paper-api.alpaca.markets`

**Authentication:**
- Header: `APCA-API-KEY-ID: {api_key}`
- Header: `APCA-API-SECRET-KEY: {secret_key}`

**Key Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v2/account` | GET | Get account info (buying power, equity, etc.) |
| `/v2/orders` | POST | Submit an order |
| `/v2/orders` | GET | List orders |
| `/v2/positions` | GET | List current positions |
| `/v2/positions/{symbol}` | GET | Get position for symbol |
| `/v2/positions/{symbol}` | DELETE | Close position |

**Market Data (free tier uses IEX):**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v2/stocks/{symbol}/bars` | GET | Get OHLCV bars |
| `/v2/stocks/{symbol}/quotes/latest` | GET | Get latest quote |
| `/v2/stocks/{symbol}/trades/latest` | GET | Get latest trade |

**Note:** Try using `alpaca-py` SDK first. If it doesn't work in Pyodide, fall back to raw httpx calls to these endpoints.

```python
# Attempt 1: Try alpaca-py
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

client = TradingClient(api_key, secret_key, paper=True)

# Attempt 2: Fall back to httpx if needed
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://paper-api.alpaca.markets/v2/account",
        headers={
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key
        }
    )
```

---

## Database Schema (D1/SQLite)

```sql
-- Algorithm configurations
CREATE TABLE algorithms (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    strategy_type TEXT NOT NULL,  -- 'sma_crossover', 'rsi', 'momentum', etc.
    config JSON NOT NULL,          -- strategy-specific parameters
    symbols JSON NOT NULL,         -- ["AAPL", "GOOGL", ...]
    enabled INTEGER DEFAULT 1,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Example config for SMA crossover:
-- {"short_period": 10, "long_period": 50, "position_size_pct": 0.1}

-- Trade execution log
CREATE TABLE trades (
    id TEXT PRIMARY KEY,
    algorithm_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,            -- 'buy' or 'sell'
    quantity REAL NOT NULL,
    price REAL,                    -- fill price (null if not filled)
    order_type TEXT NOT NULL,      -- 'market', 'limit'
    status TEXT NOT NULL,          -- 'submitted', 'filled', 'canceled', 'rejected'
    alpaca_order_id TEXT,
    submitted_at TEXT DEFAULT CURRENT_TIMESTAMP,
    filled_at TEXT,
    notes TEXT,                    -- reason for trade
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id)
);

-- Daily portfolio snapshots for each algorithm
CREATE TABLE snapshots (
    id TEXT PRIMARY KEY,
    algorithm_id TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    equity REAL NOT NULL,
    cash REAL NOT NULL,
    buying_power REAL,
    daily_pnl REAL,
    total_pnl REAL,
    positions JSON,                -- [{"symbol": "AAPL", "qty": 10, "market_value": 1500}, ...]
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (algorithm_id) REFERENCES algorithms(id),
    UNIQUE(algorithm_id, snapshot_date)
);

-- Current positions per algorithm (denormalized for fast access)
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
CREATE INDEX idx_snapshots_algorithm_date ON snapshots(algorithm_id, snapshot_date);
CREATE INDEX idx_positions_algorithm ON positions(algorithm_id);
```

---

## Worker 1: Trading Engine

**File:** `trading-engine/src/entry.py`

### Responsibilities

1. Run on cron schedule (every 1 minute during market hours)
2. Check if market is open
3. For each enabled algorithm:
   - Fetch current market data
   - Evaluate strategy conditions
   - Execute trades if conditions met
   - Log trades to D1
4. Take daily snapshots at market close

### Cron Configuration

```toml
# wrangler.toml
name = "trading-engine"
main = "src/entry.py"
compatibility_date = "2025-01-01"
compatibility_flags = ["python_workers"]

[triggers]
crons = ["*/1 * * * *"]  # Every minute

[[d1_databases]]
binding = "DB"
database_name = "paper-trading"
database_id = "<your-database-id>"

[vars]
ALPACA_API_KEY = ""      # Set via wrangler secret
ALPACA_SECRET_KEY = ""   # Set via wrangler secret
```

### Core Logic

```python
from workers import WorkerEntrypoint, Response
import httpx
import json
from datetime import datetime, timezone
import uuid

class Default(WorkerEntrypoint):

    async def scheduled(self, event, env):
        """Cron trigger handler - runs every minute"""

        # Check if market is open (simple check - enhance later)
        if not await self.is_market_open(env):
            return

        # Get all enabled algorithms
        algorithms = await self.get_enabled_algorithms(env)

        for algo in algorithms:
            try:
                await self.run_algorithm(algo, env)
            except Exception as e:
                # Log error but continue with other algorithms
                print(f"Error running algorithm {algo['id']}: {e}")

        # Take daily snapshot if market just closed
        # (implement time check logic)

    async def is_market_open(self, env) -> bool:
        """Check if US stock market is currently open"""
        # Call Alpaca clock endpoint
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://paper-api.alpaca.markets/v2/clock",
                headers=self.get_alpaca_headers(env)
            )
            data = response.json()
            return data.get("is_open", False)

    async def run_algorithm(self, algo: dict, env):
        """Execute a single algorithm's logic"""
        strategy_type = algo["strategy_type"]
        config = json.loads(algo["config"])
        symbols = json.loads(algo["symbols"])

        # Dispatch to appropriate strategy handler
        if strategy_type == "sma_crossover":
            await self.run_sma_crossover(algo, config, symbols, env)
        elif strategy_type == "rsi":
            await self.run_rsi_strategy(algo, config, symbols, env)
        # Add more strategies...

    async def run_sma_crossover(self, algo, config, symbols, env):
        """Simple Moving Average crossover strategy"""
        short_period = config.get("short_period", 10)
        long_period = config.get("long_period", 50)
        position_size_pct = config.get("position_size_pct", 0.1)

        for symbol in symbols:
            # Get historical bars
            bars = await self.get_bars(symbol, long_period + 5, env)

            if len(bars) < long_period:
                continue

            # Calculate SMAs
            closes = [b["c"] for b in bars]
            short_sma = sum(closes[-short_period:]) / short_period
            long_sma = sum(closes[-long_period:]) / long_period

            # Get current position
            position = await self.get_position(algo["id"], symbol, env)

            # Generate signals
            if short_sma > long_sma and not position:
                # Buy signal
                await self.submit_order(algo, symbol, "buy", position_size_pct, env)
            elif short_sma < long_sma and position:
                # Sell signal
                await self.submit_order(algo, symbol, "sell", position["quantity"], env)

    async def get_bars(self, symbol: str, limit: int, env) -> list:
        """Fetch OHLCV bars from Alpaca"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://data.alpaca.markets/v2/stocks/{symbol}/bars",
                headers=self.get_alpaca_headers(env),
                params={
                    "timeframe": "1Day",
                    "limit": limit,
                    "feed": "iex"  # Free tier
                }
            )
            data = response.json()
            return data.get("bars", [])

    async def submit_order(self, algo, symbol, side, quantity_or_pct, env):
        """Submit order to Alpaca and log to D1"""
        # Calculate quantity based on buying power if percentage
        # ... implementation

        order_data = {
            "symbol": symbol,
            "qty": quantity,
            "side": side,
            "type": "market",
            "time_in_force": "day"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://paper-api.alpaca.markets/v2/orders",
                headers=self.get_alpaca_headers(env),
                json=order_data
            )
            result = response.json()

        # Log to D1
        trade_id = str(uuid.uuid4())
        await env.DB.prepare("""
            INSERT INTO trades (id, algorithm_id, symbol, side, quantity, order_type, status, alpaca_order_id, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """).bind(
            trade_id,
            algo["id"],
            symbol,
            side,
            quantity,
            "market",
            result.get("status", "submitted"),
            result.get("id"),
            f"SMA crossover signal"
        ).run()

    def get_alpaca_headers(self, env) -> dict:
        return {
            "APCA-API-KEY-ID": env.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": env.ALPACA_SECRET_KEY
        }

    # Helper methods for D1 queries...
    async def get_enabled_algorithms(self, env) -> list:
        result = await env.DB.prepare(
            "SELECT * FROM algorithms WHERE enabled = 1"
        ).all()
        return result.results

    async def get_position(self, algorithm_id, symbol, env):
        result = await env.DB.prepare(
            "SELECT * FROM positions WHERE algorithm_id = ? AND symbol = ?"
        ).bind(algorithm_id, symbol).first()
        return result
```

---

## Worker 2: Dashboard API

**File:** `dashboard-api/src/entry.py`

### Responsibilities

1. Provide REST API for the frontend
2. CRUD operations for algorithms
3. Query trades, snapshots, positions
4. Calculate performance metrics

### Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/algorithms` | List all algorithms |
| POST | `/api/algorithms` | Create new algorithm |
| GET | `/api/algorithms/{id}` | Get algorithm details |
| PUT | `/api/algorithms/{id}` | Update algorithm |
| DELETE | `/api/algorithms/{id}` | Delete algorithm |
| GET | `/api/algorithms/{id}/trades` | Get trades for algorithm |
| GET | `/api/algorithms/{id}/snapshots` | Get snapshots for algorithm |
| GET | `/api/algorithms/{id}/positions` | Get current positions |
| GET | `/api/algorithms/{id}/performance` | Get calculated metrics |
| GET | `/api/comparison` | Compare all algorithms |
| GET | `/api/account` | Get Alpaca account info |

### Implementation with FastAPI

```python
from workers import WorkerEntrypoint, Response
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid

app = FastAPI()

class AlgorithmCreate(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_type: str
    config: dict
    symbols: List[str]
    enabled: bool = True

class AlgorithmUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[dict] = None
    symbols: Optional[List[str]] = None
    enabled: Optional[bool] = None

# Dependency injection for env will need to be handled
# This is pseudocode - adapt to actual Cloudflare Python Workers patterns

@app.get("/api/algorithms")
async def list_algorithms(env):
    result = await env.DB.prepare("SELECT * FROM algorithms ORDER BY created_at DESC").all()
    algorithms = []
    for row in result.results:
        algo = dict(row)
        algo["config"] = json.loads(algo["config"])
        algo["symbols"] = json.loads(algo["symbols"])
        algorithms.append(algo)
    return {"algorithms": algorithms}

@app.post("/api/algorithms")
async def create_algorithm(algo: AlgorithmCreate, env):
    algo_id = str(uuid.uuid4())
    await env.DB.prepare("""
        INSERT INTO algorithms (id, name, description, strategy_type, config, symbols, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """).bind(
        algo_id,
        algo.name,
        algo.description,
        algo.strategy_type,
        json.dumps(algo.config),
        json.dumps(algo.symbols),
        1 if algo.enabled else 0
    ).run()
    return {"id": algo_id, "message": "Algorithm created"}

@app.get("/api/algorithms/{algo_id}")
async def get_algorithm(algo_id: str, env):
    result = await env.DB.prepare(
        "SELECT * FROM algorithms WHERE id = ?"
    ).bind(algo_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Algorithm not found")
    algo = dict(result)
    algo["config"] = json.loads(algo["config"])
    algo["symbols"] = json.loads(algo["symbols"])
    return algo

@app.get("/api/algorithms/{algo_id}/trades")
async def get_algorithm_trades(algo_id: str, limit: int = 100, env):
    result = await env.DB.prepare("""
        SELECT * FROM trades
        WHERE algorithm_id = ?
        ORDER BY submitted_at DESC
        LIMIT ?
    """).bind(algo_id, limit).all()
    return {"trades": result.results}

@app.get("/api/algorithms/{algo_id}/performance")
async def get_algorithm_performance(algo_id: str, env):
    """Calculate performance metrics from snapshots"""
    snapshots = await env.DB.prepare("""
        SELECT * FROM snapshots
        WHERE algorithm_id = ?
        ORDER BY snapshot_date ASC
    """).bind(algo_id).all()

    if not snapshots.results:
        return {"error": "No snapshots available"}

    snapshots_list = snapshots.results

    # Calculate metrics
    initial_equity = snapshots_list[0]["equity"]
    final_equity = snapshots_list[-1]["equity"]
    total_return = (final_equity - initial_equity) / initial_equity * 100

    # Daily returns for Sharpe ratio
    daily_returns = []
    for i in range(1, len(snapshots_list)):
        prev_equity = snapshots_list[i-1]["equity"]
        curr_equity = snapshots_list[i]["equity"]
        daily_returns.append((curr_equity - prev_equity) / prev_equity)

    # Sharpe ratio (annualized, assuming 252 trading days)
    if daily_returns:
        avg_return = sum(daily_returns) / len(daily_returns)
        std_return = (sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)) ** 0.5
        sharpe_ratio = (avg_return / std_return) * (252 ** 0.5) if std_return > 0 else 0
    else:
        sharpe_ratio = 0

    # Max drawdown
    peak = snapshots_list[0]["equity"]
    max_drawdown = 0
    for snap in snapshots_list:
        if snap["equity"] > peak:
            peak = snap["equity"]
        drawdown = (peak - snap["equity"]) / peak
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    # Win rate from trades
    trades = await env.DB.prepare("""
        SELECT * FROM trades WHERE algorithm_id = ? AND status = 'filled'
    """).bind(algo_id).all()

    # Simplified win rate calculation
    # (In reality, need to pair buy/sell trades to calculate P&L per trade)

    return {
        "algorithm_id": algo_id,
        "initial_equity": initial_equity,
        "final_equity": final_equity,
        "total_return_pct": round(total_return, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "max_drawdown_pct": round(max_drawdown * 100, 2),
        "total_trades": len(trades.results),
        "days_active": len(snapshots_list)
    }

@app.get("/api/comparison")
async def compare_algorithms(env):
    """Get comparison metrics for all algorithms"""
    algorithms = await env.DB.prepare("SELECT id, name FROM algorithms").all()

    comparison = []
    for algo in algorithms.results:
        perf = await get_algorithm_performance(algo["id"], env)
        perf["name"] = algo["name"]
        comparison.append(perf)

    # Sort by total return
    comparison.sort(key=lambda x: x.get("total_return_pct", 0), reverse=True)

    return {"comparison": comparison}


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        # Route to FastAPI app
        # Note: Actual integration pattern may differ - check Cloudflare docs
        return await app(request)
```

---

## Frontend (Cloudflare Pages)

### Structure

```
frontend/
├── index.html
├── css/
│   └── styles.css
├── js/
│   ├── app.js
│   ├── api.js
│   └── charts.js
└── pages/
    ├── algorithms.html
    ├── comparison.html
    └── algorithm-detail.html
```

### Key Features

1. **Dashboard Home**
   - Overview cards showing total algorithms, best performer, worst performer
   - Equity curves chart (all algorithms overlaid)
   - Recent trades table

2. **Algorithm Management**
   - List view with enable/disable toggles
   - Create new algorithm form with strategy selector
   - Edit algorithm configuration

3. **Algorithm Detail View**
   - Equity curve chart
   - Performance metrics card
   - Trades history table
   - Current positions table

4. **Comparison View**
   - Side-by-side metrics table
   - Overlay equity curves
   - Risk/return scatter plot

### Chart Library

Use Chart.js (can load from CDN):

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
```

### Example Dashboard Component

```javascript
// js/api.js
const API_BASE = '/api';  // Same origin, proxied to dashboard-api worker

async function fetchAlgorithms() {
    const response = await fetch(`${API_BASE}/algorithms`);
    return response.json();
}

async function fetchComparison() {
    const response = await fetch(`${API_BASE}/comparison`);
    return response.json();
}

async function fetchAlgorithmSnapshots(algoId) {
    const response = await fetch(`${API_BASE}/algorithms/${algoId}/snapshots`);
    return response.json();
}

async function createAlgorithm(data) {
    const response = await fetch(`${API_BASE}/algorithms`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    return response.json();
}

// js/charts.js
function renderEquityChart(canvasId, algorithmsData) {
    const ctx = document.getElementById(canvasId).getContext('2d');

    const datasets = algorithmsData.map((algo, index) => ({
        label: algo.name,
        data: algo.snapshots.map(s => ({ x: s.snapshot_date, y: s.equity })),
        borderColor: getColor(index),
        fill: false,
        tension: 0.1
    }));

    new Chart(ctx, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            scales: {
                x: { type: 'time', time: { unit: 'day' } },
                y: { beginAtZero: false }
            }
        }
    });
}

function getColor(index) {
    const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
    return colors[index % colors.length];
}
```

---

## Built-in Strategies to Implement

### 1. SMA Crossover

**Config:**
```json
{
    "short_period": 10,
    "long_period": 50,
    "position_size_pct": 0.1
}
```

**Logic:** Buy when short SMA crosses above long SMA, sell when it crosses below.

### 2. RSI Mean Reversion

**Config:**
```json
{
    "period": 14,
    "oversold": 30,
    "overbought": 70,
    "position_size_pct": 0.1
}
```

**Logic:** Buy when RSI < oversold, sell when RSI > overbought.

### 3. Momentum

**Config:**
```json
{
    "lookback_days": 20,
    "threshold_pct": 5,
    "position_size_pct": 0.1
}
```

**Logic:** Buy if price up more than threshold% over lookback period, sell if down more than threshold%.

### 4. Buy and Hold (Benchmark)

**Config:**
```json
{
    "position_size_pct": 1.0
}
```

**Logic:** Buy on first run, hold forever. Useful as a benchmark.

---

## Deployment Steps

### 1. Set up Cloudflare Account

```bash
# Install wrangler
npm install -g wrangler

# Login
wrangler login
```

### 2. Create D1 Database

```bash
# Create database
wrangler d1 create paper-trading

# Note the database_id from output

# Apply schema
wrangler d1 execute paper-trading --file=./schema.sql
```

### 3. Deploy Trading Engine

```bash
cd trading-engine

# Set secrets
wrangler secret put ALPACA_API_KEY
wrangler secret put ALPACA_SECRET_KEY

# Deploy
uv run pywrangler deploy
```

### 4. Deploy Dashboard API

```bash
cd dashboard-api
uv run pywrangler deploy
```

### 5. Deploy Frontend

```bash
cd frontend
wrangler pages deploy .
```

### 6. Configure Routes

Set up routes so `/api/*` goes to dashboard-api worker and `/*` goes to Pages.

---

## Testing Checklist

- [ ] Trading engine cron fires correctly
- [ ] Market hours check works (skips when market closed)
- [ ] Can create algorithm via API
- [ ] Can fetch market data from Alpaca
- [ ] Orders submit successfully to Alpaca paper account
- [ ] Trades logged to D1
- [ ] Snapshots created at end of day
- [ ] Dashboard displays algorithms
- [ ] Equity chart renders
- [ ] Performance metrics calculate correctly
- [ ] Comparison view works

---

## Environment Variables / Secrets

| Name | Where | Description |
|------|-------|-------------|
| `ALPACA_API_KEY` | Wrangler secret | Alpaca paper trading API key |
| `ALPACA_SECRET_KEY` | Wrangler secret | Alpaca paper trading secret |

Get these from: https://app.alpaca.markets → Paper Trading → API Keys

---

## Future Enhancements (Out of Scope for V1)

- WebSocket streaming for real-time prices
- More sophisticated strategies (pairs trading, ML-based)
- Backtesting engine
- Email/Discord alerts on trades
- Multiple paper trading accounts per algorithm
- User authentication
- Position sizing algorithms (Kelly criterion, etc.)

---

## Notes for Implementation

1. **Python Workers are in beta** - check latest Cloudflare docs for any syntax changes
2. **alpaca-py compatibility** - test first, fall back to httpx if needed
3. **D1 is serverless SQLite** - no persistent connections, each query is independent
4. **Cron minimum is 1 minute** - can't do sub-minute execution
5. **Market hours** - US market is 9:30 AM - 4:00 PM ET, check with Alpaca clock API
6. **Rate limits** - Alpaca has rate limits, be mindful with multiple algorithms

---

## File Structure

```
paper-trading-platform/
├── README.md
├── schema.sql
├── trading-engine/
│   ├── pyproject.toml
│   ├── wrangler.toml
│   └── src/
│       ├── entry.py
│       ├── strategies/
│       │   ├── __init__.py
│       │   ├── sma_crossover.py
│       │   ├── rsi.py
│       │   └── momentum.py
│       └── utils/
│           ├── __init__.py
│           ├── alpaca.py
│           └── db.py
├── dashboard-api/
│   ├── pyproject.toml
│   ├── wrangler.toml
│   └── src/
│       ├── entry.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── algorithms.py
│       │   └── performance.py
│       └── utils/
│           └── metrics.py
└── frontend/
    ├── index.html
    ├── wrangler.toml (for Pages)
    ├── css/
    │   └── styles.css
    └── js/
        ├── app.js
        ├── api.js
        └── charts.js
```
