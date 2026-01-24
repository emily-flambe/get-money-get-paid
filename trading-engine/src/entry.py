"""
Trading Engine Worker
Runs on cron schedule to execute trading algorithms against Alpaca paper trading API.
"""
from js import fetch, Response, Headers, JSON, Request, Object
from pyodide.ffi import to_js, create_proxy
import json
import uuid
from datetime import datetime, timezone


async def on_scheduled(event, env, ctx):
    """Cron trigger handler - runs every minute during market hours"""
    try:
        # Check if market is open
        if not await is_market_open(env):
            return Response.new("Market closed, skipping")

        # Check if we should create hourly snapshots (at the top of each hour)
        now = datetime.now(timezone.utc)
        if now.minute == 0:
            await create_snapshots_for_all(env, trigger="hourly")

        # Get all enabled algorithms
        algorithms = await get_enabled_algorithms(env)

        for algo in algorithms:
            try:
                await run_algorithm(algo, env)
            except Exception as e:
                print(f"Error running algorithm {algo['id']}: {e}")

        return Response.new("Trading engine run complete")
    except Exception as e:
        print(f"Trading engine error: {e}")
        return Response.new(f"Error: {e}", status=500)


async def on_fetch(request, env, ctx):
    """HTTP handler for manual triggers and health checks"""
    url = request.url
    headers_json = Headers.new({"Content-Type": "application/json"}.items())

    if "/health" in url:
        return Response.new(json.dumps({"status": "ok"}), headers=headers_json)

    if "/status" in url:
        # Check Alpaca connection and market status
        try:
            # Check if secrets are available
            api_key = getattr(env, 'ALPACA_API_KEY', None)
            secret_key = getattr(env, 'ALPACA_SECRET_KEY', None)

            if not api_key or not secret_key:
                return Response.new(json.dumps({
                    "error": "Alpaca credentials not configured",
                    "has_api_key": api_key is not None,
                    "has_secret_key": secret_key is not None
                }), status=500, headers=headers_json)

            # Use alpaca_fetch helper for authenticated requests
            clock_resp = await alpaca_fetch("https://paper-api.alpaca.markets/v2/clock", env)
            clock_status = clock_resp.status
            clock_text = await clock_resp.text()

            if clock_status != 200:
                # Debug info for troubleshooting
                api_key_str = str(api_key)
                secret_key_str = str(secret_key)
                return Response.new(json.dumps({
                    "error": "Alpaca clock API error",
                    "status": clock_status,
                    "response": clock_text[:500] if clock_text else "empty",
                    "api_key_len": len(api_key_str),
                    "secret_key_len": len(secret_key_str),
                    "api_key_repr": repr(api_key_str[:20]) if len(api_key_str) >= 20 else repr(api_key_str)
                }), status=500, headers=headers_json)

            clock = json.loads(clock_text) if clock_text else {}

            account_resp = await alpaca_fetch("https://paper-api.alpaca.markets/v2/account", env)
            account_text = await account_resp.text()
            account = json.loads(account_text) if account_text else {}

            algorithms = await get_enabled_algorithms(env)

            return Response.new(json.dumps({
                "alpaca_connected": "id" in account,
                "market_open": clock.get("is_open", False),
                "next_open": clock.get("next_open"),
                "next_close": clock.get("next_close"),
                "account_equity": account.get("equity"),
                "account_buying_power": account.get("buying_power"),
                "account_status": account.get("status"),
                "enabled_algorithms": len(algorithms),
                "algorithm_names": [a["name"] for a in algorithms]
            }), headers=headers_json)
        except Exception as e:
            import traceback
            return Response.new(json.dumps({"error": str(e), "type": type(e).__name__}), status=500, headers=headers_json)

    if "/test" in url:
        # Force run regardless of market status (for testing)
        try:
            algorithms = await get_enabled_algorithms(env)
            results = []
            for algo in algorithms:
                try:
                    await run_algorithm(algo, env)
                    results.append({"algorithm": algo["name"], "status": "executed"})
                except Exception as e:
                    results.append({"algorithm": algo["name"], "status": "error", "error": str(e)})
            return Response.new(json.dumps({"test_run": True, "results": results}), headers=headers_json)
        except Exception as e:
            return Response.new(json.dumps({"error": str(e)}), status=500, headers=headers_json)

    if "/run" in url:
        return await on_scheduled(None, env, ctx)

    return Response.new("Trading Engine Worker", status=200)


async def is_market_open(env) -> bool:
    """Check if US stock market is currently open using Alpaca clock API"""
    try:
        response = await alpaca_fetch("https://paper-api.alpaca.markets/v2/clock", env)
        data = json.loads(await response.text())
        return data.get("is_open", False)
    except Exception as e:
        print(f"Error checking market status: {e}")
        return False


def js_to_py(obj):
    """Convert JsProxy object to Python dict/list"""
    if hasattr(obj, 'to_py'):
        return obj.to_py()
    return obj


async def get_enabled_algorithms(env) -> list:
    """Fetch all enabled algorithms from D1"""
    try:
        result = await env.DB.prepare(
            "SELECT * FROM algorithms WHERE enabled = 1"
        ).all()

        algorithms = []
        results = js_to_py(result.results)
        for row in results:
            algo = js_to_py(row) if hasattr(row, 'to_py') else dict(row)
            algo["config"] = json.loads(algo["config"]) if isinstance(algo["config"], str) else algo["config"]
            algo["symbols"] = json.loads(algo["symbols"]) if isinstance(algo["symbols"], str) else algo["symbols"]
            algorithms.append(algo)
        return algorithms
    except Exception as e:
        print(f"Error fetching algorithms: {e}")
        return []


async def run_algorithm(algo: dict, env):
    """Execute a single algorithm's logic"""
    strategy_type = algo["strategy_type"]
    config = algo["config"]
    symbols = algo["symbols"]

    if strategy_type == "sma_crossover":
        await run_sma_crossover(algo, config, symbols, env)
    elif strategy_type == "rsi":
        await run_rsi_strategy(algo, config, symbols, env)
    elif strategy_type == "momentum":
        await run_momentum_strategy(algo, config, symbols, env)
    elif strategy_type == "buy_and_hold":
        await run_buy_and_hold(algo, config, symbols, env)


async def run_sma_crossover(algo, config, symbols, env):
    """Simple Moving Average crossover strategy"""
    short_period = config.get("short_period", 10)
    long_period = config.get("long_period", 50)
    position_size_pct = config.get("position_size_pct", 0.1)

    for symbol in symbols:
        bars = await get_bars(symbol, long_period + 5, env)

        if len(bars) < long_period:
            continue

        closes = [b["c"] for b in bars]
        short_sma = sum(closes[-short_period:]) / short_period
        long_sma = sum(closes[-long_period:]) / long_period

        position = await get_position(algo["id"], symbol, env)

        if short_sma > long_sma and not position:
            # Buy signal
            await submit_order(algo, symbol, "buy", position_size_pct, env, "SMA crossover buy signal")
        elif short_sma < long_sma and position:
            # Sell signal
            await submit_order(algo, symbol, "sell", position["quantity"], env, "SMA crossover sell signal")


async def run_rsi_strategy(algo, config, symbols, env):
    """RSI mean reversion strategy"""
    period = config.get("period", 14)
    oversold = config.get("oversold", 30)
    overbought = config.get("overbought", 70)
    position_size_pct = config.get("position_size_pct", 0.1)

    for symbol in symbols:
        bars = await get_bars(symbol, period + 5, env)

        if len(bars) < period + 1:
            continue

        rsi = calculate_rsi(bars, period)
        position = await get_position(algo["id"], symbol, env)

        if rsi < oversold and not position:
            await submit_order(algo, symbol, "buy", position_size_pct, env, f"RSI oversold ({rsi:.1f})")
        elif rsi > overbought and position:
            await submit_order(algo, symbol, "sell", position["quantity"], env, f"RSI overbought ({rsi:.1f})")


def calculate_rsi(bars, period):
    """Calculate RSI from price bars"""
    closes = [b["c"] for b in bars]
    gains = []
    losses = []

    for i in range(1, len(closes)):
        change = closes[i] - closes[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


async def run_momentum_strategy(algo, config, symbols, env):
    """Momentum strategy"""
    lookback_days = config.get("lookback_days", 20)
    threshold_pct = config.get("threshold_pct", 5)
    position_size_pct = config.get("position_size_pct", 0.1)

    for symbol in symbols:
        bars = await get_bars(symbol, lookback_days + 1, env)

        if len(bars) < lookback_days:
            continue

        start_price = bars[0]["c"]
        end_price = bars[-1]["c"]
        momentum_pct = ((end_price - start_price) / start_price) * 100

        position = await get_position(algo["id"], symbol, env)

        if momentum_pct > threshold_pct and not position:
            await submit_order(algo, symbol, "buy", position_size_pct, env, f"Momentum buy ({momentum_pct:.1f}%)")
        elif momentum_pct < -threshold_pct and position:
            await submit_order(algo, symbol, "sell", position["quantity"], env, f"Momentum sell ({momentum_pct:.1f}%)")


async def run_buy_and_hold(algo, config, symbols, env):
    """Buy and hold benchmark strategy"""
    position_size_pct = config.get("position_size_pct", 1.0)

    for symbol in symbols:
        position = await get_position(algo["id"], symbol, env)
        if not position:
            await submit_order(algo, symbol, "buy", position_size_pct, env, "Buy and hold initial purchase")


async def get_bars(symbol: str, limit: int, env) -> list:
    """Fetch OHLCV bars from Alpaca"""
    try:
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars?timeframe=1Day&limit={limit}&feed=iex"
        response = await alpaca_fetch(url, env)
        data = json.loads(await response.text())
        bars = data.get("bars", []) or []

        # If bars empty (market closed), try latest trade as fallback
        if not bars:
            latest = await get_latest_price(symbol, env)
            if latest > 0:
                # Create a synthetic bar with the latest price
                bars = [{"c": latest, "o": latest, "h": latest, "l": latest, "v": 0}]

        return bars
    except Exception as e:
        print(f"Error fetching bars for {symbol}: {e}")
        return []


async def get_latest_price(symbol: str, env) -> float:
    """Get latest trade price from Alpaca (works when market is closed)"""
    try:
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
        response = await alpaca_fetch(url, env)
        data = json.loads(await response.text())
        trade = data.get("trade", {})
        return float(trade.get("p", 0)) if trade else 0
    except Exception as e:
        print(f"Error fetching latest price for {symbol}: {e}")
        return 0


async def get_position(algorithm_id: str, symbol: str, env):
    """Get current position for algorithm/symbol from D1"""
    try:
        result = await env.DB.prepare(
            "SELECT * FROM positions WHERE algorithm_id = ? AND symbol = ?"
        ).bind(algorithm_id, symbol).first()
        if not result:
            return None
        return js_to_py(result) if hasattr(result, 'to_py') else dict(result)
    except Exception as e:
        print(f"Error fetching position: {e}")
        return None


async def get_account(env) -> dict:
    """Get Alpaca account info"""
    try:
        response = await alpaca_fetch("https://paper-api.alpaca.markets/v2/account", env)
        return json.loads(await response.text())
    except Exception as e:
        print(f"Error fetching account: {e}")
        return {}


async def get_algorithm_cash(algorithm_id: str, env) -> float:
    """Get algorithm's available cash from D1"""
    try:
        result = await env.DB.prepare(
            "SELECT cash FROM algorithms WHERE id = ?"
        ).bind(algorithm_id).first()
        if not result:
            return 0.0
        row = js_to_py(result) if hasattr(result, 'to_py') else dict(result)
        return float(row.get("cash", 0))
    except Exception as e:
        print(f"Error fetching algorithm cash: {e}")
        return 0.0


async def update_algorithm_cash(algorithm_id: str, new_cash: float, env):
    """Update algorithm's cash balance in D1"""
    try:
        await env.DB.prepare(
            "UPDATE algorithms SET cash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        ).bind(new_cash, algorithm_id).run()
    except Exception as e:
        print(f"Error updating algorithm cash: {e}")


async def submit_order(algo, symbol, side, quantity_or_pct, env, notes=""):
    """Submit order to Alpaca and log to D1"""
    try:
        # Get algorithm's available cash
        algorithm_cash = await get_algorithm_cash(algo["id"], env)

        # Get current price for quantity calculations
        bars = await get_bars(symbol, 1, env)
        if not bars:
            return
        current_price = bars[-1]["c"]

        # Calculate quantity
        if side == "buy" and isinstance(quantity_or_pct, float) and quantity_or_pct <= 1:
            # Position size as percentage of algorithm's cash
            dollar_amount = algorithm_cash * quantity_or_pct
            quantity = int(dollar_amount / current_price)
        else:
            quantity = int(quantity_or_pct)

        if quantity <= 0:
            return

        # For BUY: Check if algorithm has enough cash
        if side == "buy":
            estimated_cost = quantity * current_price
            if estimated_cost > algorithm_cash:
                print(f"Insufficient cash for {algo['name']}: need ${estimated_cost:.2f}, have ${algorithm_cash:.2f}")
                return

        # Submit order to Alpaca
        order_data = {
            "symbol": symbol,
            "qty": str(quantity),
            "side": side,
            "type": "market",
            "time_in_force": "day"
        }

        response = await alpaca_fetch(
            "https://paper-api.alpaca.markets/v2/orders",
            env,
            method="POST",
            body=order_data
        )
        result = json.loads(await response.text())

        # Log trade to D1
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
            result.get("id", ""),
            notes
        ).run()

        # Update positions table
        if side == "buy":
            await update_position_buy(algo["id"], symbol, quantity, result, env)
        else:
            await update_position_sell(algo["id"], symbol, quantity, result, current_price, env)

        # Create snapshot after trade
        await create_snapshot(algo["id"], env, trigger="trade")

        print(f"Order submitted: {side} {quantity} {symbol} for {algo['name']}")

    except Exception as e:
        print(f"Error submitting order: {e}")


async def update_position_buy(algorithm_id, symbol, quantity, order_result, env):
    """Update or create position after buy and deduct cash"""
    try:
        existing = await get_position(algorithm_id, symbol, env)

        # Get fill price from order, or estimate from current market price
        fill_price_raw = order_result.get("filled_avg_price")
        if fill_price_raw is not None:
            fill_price = float(fill_price_raw)
        else:
            # Order not filled yet (market closed) - use current price as estimate
            bars = await get_bars(symbol, 1, env)
            fill_price = bars[-1]["c"] if bars else 0

        if existing:
            new_qty = existing["quantity"] + quantity
            # Calculate new average price
            old_value = existing["quantity"] * existing["avg_entry_price"]
            new_value = quantity * fill_price
            new_avg = (old_value + new_value) / new_qty if new_qty > 0 else 0

            await env.DB.prepare("""
                UPDATE positions SET quantity = ?, avg_entry_price = ?, updated_at = CURRENT_TIMESTAMP
                WHERE algorithm_id = ? AND symbol = ?
            """).bind(new_qty, new_avg, algorithm_id, symbol).run()
        else:
            position_id = str(uuid.uuid4())
            await env.DB.prepare("""
                INSERT INTO positions (id, algorithm_id, symbol, quantity, avg_entry_price)
                VALUES (?, ?, ?, ?, ?)
            """).bind(position_id, algorithm_id, symbol, quantity, fill_price).run()

        # Deduct cost from algorithm's cash
        cost = quantity * fill_price
        current_cash = await get_algorithm_cash(algorithm_id, env)
        new_cash = current_cash - cost
        await update_algorithm_cash(algorithm_id, new_cash, env)
        print(f"Deducted ${cost:.2f} from algorithm {algorithm_id}, new cash: ${new_cash:.2f}")

    except Exception as e:
        print(f"Error updating position: {e}")


async def update_position_sell(algorithm_id, symbol, quantity, order_result, current_price, env):
    """Update or remove position after sell and add proceeds to cash"""
    try:
        existing = await get_position(algorithm_id, symbol, env)
        if existing:
            new_qty = existing["quantity"] - quantity
            if new_qty <= 0:
                await env.DB.prepare(
                    "DELETE FROM positions WHERE algorithm_id = ? AND symbol = ?"
                ).bind(algorithm_id, symbol).run()
            else:
                await env.DB.prepare("""
                    UPDATE positions SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE algorithm_id = ? AND symbol = ?
                """).bind(new_qty, algorithm_id, symbol).run()

            # Get fill price from order, or use current price as estimate
            fill_price_raw = order_result.get("filled_avg_price")
            if fill_price_raw is not None:
                fill_price = float(fill_price_raw)
            else:
                fill_price = current_price

            # Add proceeds to algorithm's cash
            proceeds = quantity * fill_price
            algo_cash = await get_algorithm_cash(algorithm_id, env)
            new_cash = algo_cash + proceeds
            await update_algorithm_cash(algorithm_id, new_cash, env)
            print(f"Added ${proceeds:.2f} to algorithm {algorithm_id}, new cash: ${new_cash:.2f}")

    except Exception as e:
        print(f"Error updating position: {e}")


async def create_snapshot(algorithm_id: str, env, trigger: str = "trade"):
    """Create a snapshot of algorithm's current equity state"""
    try:
        # Get algorithm's cash balance
        algorithm_cash = await get_algorithm_cash(algorithm_id, env)

        # Get all positions for this algorithm
        result = await env.DB.prepare(
            "SELECT * FROM positions WHERE algorithm_id = ?"
        ).bind(algorithm_id).all()

        positions_list = []
        results = js_to_py(result.results)

        total_position_value = 0.0
        total_cost_basis = 0.0

        for row in results:
            pos = js_to_py(row) if hasattr(row, 'to_py') else dict(row)
            symbol = pos["symbol"]
            quantity = float(pos["quantity"])
            avg_entry = float(pos["avg_entry_price"]) if pos.get("avg_entry_price") else 0

            # Get current price
            bars = await get_bars(symbol, 1, env)
            current_price = bars[-1]["c"] if bars else avg_entry

            market_value = quantity * current_price
            cost_basis = quantity * avg_entry
            unrealized_pnl = market_value - cost_basis

            total_position_value += market_value
            total_cost_basis += cost_basis

            positions_list.append({
                "symbol": symbol,
                "quantity": quantity,
                "avg_entry_price": avg_entry,
                "current_price": current_price,
                "market_value": round(market_value, 2),
                "unrealized_pnl": round(unrealized_pnl, 2)
            })

        # Total equity = cash + position market values
        total_equity = algorithm_cash + total_position_value
        total_pnl = total_equity - total_cost_basis

        # Get today's date for snapshot_date field
        now = datetime.utcnow()
        snapshot_date = now.strftime("%Y-%m-%d")

        # Insert snapshot
        snapshot_id = str(uuid.uuid4())
        await env.DB.prepare("""
            INSERT INTO snapshots (id, algorithm_id, snapshot_date, equity, cash, buying_power, daily_pnl, total_pnl, positions)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """).bind(
            snapshot_id,
            algorithm_id,
            snapshot_date,
            round(total_equity, 2),
            round(algorithm_cash, 2),
            round(algorithm_cash, 2),  # buying_power = cash for algorithm-level tracking
            0,  # daily_pnl - would need previous day's snapshot to calculate
            round(total_pnl, 2),
            json.dumps(positions_list)
        ).run()

        print(f"Snapshot created for algorithm {algorithm_id}: equity=${total_equity:.2f}, cash=${algorithm_cash:.2f}, trigger={trigger}")

    except Exception as e:
        print(f"Error creating snapshot: {e}")


async def create_snapshots_for_all(env, trigger: str = "hourly"):
    """Create snapshots for all enabled algorithms"""
    try:
        algorithms = await get_enabled_algorithms(env)
        for algo in algorithms:
            await create_snapshot(algo["id"], env, trigger)
        print(f"Created {len(algorithms)} snapshots (trigger={trigger})")
    except Exception as e:
        print(f"Error creating snapshots for all: {e}")


def get_alpaca_headers(env):
    """Get Alpaca API authentication headers as a new Headers object"""
    h = Headers.new()
    h.set("APCA-API-KEY-ID", str(env.ALPACA_API_KEY))
    h.set("APCA-API-SECRET-KEY", str(env.ALPACA_SECRET_KEY))
    h.set("Content-Type", "application/json")
    return h


async def alpaca_fetch(url: str, env, method: str = "GET", body=None):
    """Make authenticated request to Alpaca API using Request object"""
    headers = Headers.new()
    headers.set("APCA-API-KEY-ID", str(env.ALPACA_API_KEY))
    headers.set("APCA-API-SECRET-KEY", str(env.ALPACA_SECRET_KEY))
    headers.set("Content-Type", "application/json")

    # Create init object using JSON.parse to ensure it's a pure JS object
    init_dict = {"method": method}
    if body:
        init_dict["body"] = json.dumps(body) if isinstance(body, dict) else body

    init = JSON.parse(json.dumps(init_dict))
    init.headers = headers

    request = Request.new(url, init)
    return await fetch(request)
