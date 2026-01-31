# Real-time WebSocket Trading Engine Design

**Date:** 2026-01-30
**Status:** Implemented

## Overview

WebSocket-based trading system that reacts to real-time market data from Alpaca. Runs on the PC (WSL2), supervised by Dagster, with data synced to D1 for the existing dashboard.

## Goals

- **Experimentation**: Flexible infrastructure to test different trading strategies
- **Speed**: React to price movements in milliseconds instead of minutes
- **Observability**: Good logging, Dagster monitoring, easy debugging

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  WSL2 Ubuntu                                                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  trading-engine (systemd service)                        │   │
│  │                                                          │   │
│  │  WebSocket ──▶ TickBuffer ──▶ Strategies ──▶ OrderManager│   │
│  │                    │                             │        │   │
│  │                    ▼                             ▼        │   │
│  │              Local Postgres              Alpaca REST API  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│  ┌───────────────────────────┼───────────────────────────────┐ │
│  │  Dagster                  ▼                                │ │
│  │  - Health sensor (restart if dead)                        │ │
│  │  - Sync job (Postgres → D1 every 5 min)                   │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### WebSocket Client (`src/websocket.py`)
- Connects to Alpaca IEX stream
- Receives trades and 1-minute bars
- Dispatches to callbacks

### TickBuffer (`src/indicators.py`)
- Rolling window of ticks per symbol (120 seconds)
- Computes indicators incrementally:
  - Momentum at 5s, 10s, 15s, 30s, 60s intervals
  - Mean and standard deviation at 30s, 60s, 120s
  - VWAP

### Strategy Base (`src/strategies/base.py`)
- Abstract class all strategies implement
- `on_tick(symbol, price, indicators)` → Signal or None
- Built-in position tracking, cooldowns

### Included Strategies
- **MomentumStrategy**: Buy on quick price increases, sell on reversals
- **MeanReversionStrategy**: Buy oversold (z < -2), sell on reversion

### OrderManager (`src/orders.py`)
- Safety rails:
  - Rate limiting (max 10 orders/minute)
  - Per-symbol cooldown (5 seconds)
  - Position limits (max 25% of account in one symbol)
  - Paper trading enforcement
- Uses Alpaca REST API with `notional` for fractional shares

### Dagster Integration (`dagster_definitions/`)
- Health sensor: Restarts service if down
- D1 sync job: Pushes trades/positions to dashboard

## Configuration

### `config/settings.yaml`
- Alpaca credentials (via env vars)
- Postgres connection
- Safety limits

### `config/strategies.yaml`
- Strategy instances with parameters
- Enable/disable per strategy
- Cash allocation per strategy

## Deployment

1. Run `./scripts/setup.sh` from WSL2
2. Enter Alpaca API keys when prompted
3. Start with `sudo systemctl start trading-engine`

## Trade-offs

- **PC must be on during market hours** - Cloudflare worker remains as backup
- **Local Postgres, not D1** - Faster for high-volume tick storage; syncs to D1 for dashboard
- **Strategies in Python code** - Requires code changes for new strategy types, but parameters are YAML

## Future Enhancements

- [ ] Add more indicator types (RSI, Bollinger, etc.)
- [ ] Implement D1 sync jobs in Dagster
- [ ] Add backtesting mode using historical ticks
- [ ] Web UI for strategy monitoring (separate from main dashboard)
