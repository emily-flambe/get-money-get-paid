# Real-time Trading Engine

WebSocket-based trading engine that reacts to real-time market data from Alpaca.

## Architecture

```
Alpaca WebSocket ──▶ TickBuffer ──▶ Strategies ──▶ OrderManager ──▶ Alpaca REST
                         │
                         ▼
                   Local Postgres
```

- **WebSocket**: Persistent connection to Alpaca, receives trades/bars in real-time
- **TickBuffer**: Rolling window of ticks, computes indicators (momentum, VWAP, etc.)
- **Strategies**: Python classes that decide BUY/SELL based on indicators
- **OrderManager**: Executes orders with safety rails (rate limits, position limits)

## Setup (WSL2)

```bash
# From WSL2 Ubuntu
cd /mnt/c/Users/emily/Documents/GitHub/get-money-get-paid/realtime
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Running

```bash
# As systemd service
sudo systemctl start trading-engine
sudo journalctl -u trading-engine -f

# Manual (for testing)
export ALPACA_API_KEY=xxx
export ALPACA_SECRET_KEY=xxx
/opt/dagster/venv/bin/python -m src.main --log-level DEBUG
```

## Configuration

- `config/settings.yaml` - API keys, database, safety limits
- `config/strategies.yaml` - Strategy instances and parameters

## Adding Strategies

1. Create new class in `src/strategies/`:
   ```python
   from .base import Strategy, Signal, SignalType

   class MyStrategy(Strategy):
       def on_tick(self, symbol, price, indicators):
           if should_buy:
               return self._make_signal(SignalType.BUY, symbol, price, "reason")
           return None
   ```

2. Register in `src/strategies/__init__.py`:
   ```python
   STRATEGY_TYPES["my_strategy"] = MyStrategy
   ```

3. Add instance to `config/strategies.yaml`:
   ```yaml
   - type: my_strategy
     name: "My Strategy"
     symbols: [SPY]
     params:
       threshold: 0.1
   ```

## Dagster Integration

Add to `/opt/dagster/dagster_home/workspace.yaml`:

```yaml
- python_file:
    relative_path: /mnt/c/Users/emily/Documents/GitHub/get-money-get-paid/realtime/dagster_definitions/definitions.py
    location_name: trading_engine
```

Provides:
- Health sensor (restarts service if down)
- D1 sync job (pushes data to dashboard)
