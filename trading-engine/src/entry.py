"""
Trading Engine Worker
Runs on cron schedule to execute trading algorithms against Alpaca paper trading API.
"""
from js import fetch, Response, Headers, JSON
import json
import uuid
from datetime import datetime


async def on_scheduled(event, env, ctx):
    """Cron trigger handler - runs every minute during market hours"""
    try:
        # Check if market is open
        if not await is_market_open(env):
            return Response.new("Market closed, skipping")

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
    if "/health" in url:
        return Response.new(json.dumps({"status": "ok"}), headers=Headers.new({"Content-Type": "application/json"}.items()))

    if "/run" in url:
        return await on_scheduled(None, env, ctx)

    return Response.new("Trading Engine Worker", status=200)


async def is_market_open(env) -> bool:
    """Check if US stock market is currently open using Alpaca clock API"""
    try:
        headers = get_alpaca_headers(env)
        response = await fetch(
            "https://paper-api.alpaca.markets/v2/clock",
            {
                "method": "GET",
                "headers": headers
            }
        )
        data = json.loads(await response.text())
        return data.get("is_open", False)
    except Exception as e:
        print(f"Error checking market status: {e}")
        return False


async def get_enabled_algorithms(env) -> list:
    """Fetch all enabled algorithms from D1"""
    try:
        result = await env.DB.prepare(
            "SELECT * FROM algorithms WHERE enabled = 1"
        ).all()

        algorithms = []
        for row in result.results:
            algo = dict(row)
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
        headers = get_alpaca_headers(env)
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars?timeframe=1Day&limit={limit}&feed=iex"

        response = await fetch(url, {"method": "GET", "headers": headers})
        data = json.loads(await response.text())
        return data.get("bars", []) or []
    except Exception as e:
        print(f"Error fetching bars for {symbol}: {e}")
        return []


async def get_position(algorithm_id: str, symbol: str, env):
    """Get current position for algorithm/symbol from D1"""
    try:
        result = await env.DB.prepare(
            "SELECT * FROM positions WHERE algorithm_id = ? AND symbol = ?"
        ).bind(algorithm_id, symbol).first()
        return dict(result) if result else None
    except Exception as e:
        print(f"Error fetching position: {e}")
        return None


async def get_account(env) -> dict:
    """Get Alpaca account info"""
    try:
        headers = get_alpaca_headers(env)
        response = await fetch(
            "https://paper-api.alpaca.markets/v2/account",
            {"method": "GET", "headers": headers}
        )
        return json.loads(await response.text())
    except Exception as e:
        print(f"Error fetching account: {e}")
        return {}


async def submit_order(algo, symbol, side, quantity_or_pct, env, notes=""):
    """Submit order to Alpaca and log to D1"""
    try:
        account = await get_account(env)
        buying_power = float(account.get("buying_power", 0))

        # Calculate quantity
        if side == "buy" and isinstance(quantity_or_pct, float) and quantity_or_pct <= 1:
            # Position size as percentage of buying power
            bars = await get_bars(symbol, 1, env)
            if not bars:
                return
            current_price = bars[-1]["c"]
            dollar_amount = buying_power * quantity_or_pct
            quantity = int(dollar_amount / current_price)
        else:
            quantity = int(quantity_or_pct)

        if quantity <= 0:
            return

        # Submit order to Alpaca
        headers = get_alpaca_headers(env)
        order_data = {
            "symbol": symbol,
            "qty": str(quantity),
            "side": side,
            "type": "market",
            "time_in_force": "day"
        }

        response = await fetch(
            "https://paper-api.alpaca.markets/v2/orders",
            {
                "method": "POST",
                "headers": headers,
                "body": json.dumps(order_data)
            }
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
            await update_position_sell(algo["id"], symbol, quantity, env)

        print(f"Order submitted: {side} {quantity} {symbol} for {algo['name']}")

    except Exception as e:
        print(f"Error submitting order: {e}")


async def update_position_buy(algorithm_id, symbol, quantity, order_result, env):
    """Update or create position after buy"""
    try:
        existing = await get_position(algorithm_id, symbol, env)
        fill_price = float(order_result.get("filled_avg_price", 0)) or 0

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
    except Exception as e:
        print(f"Error updating position: {e}")


async def update_position_sell(algorithm_id, symbol, quantity, env):
    """Update or remove position after sell"""
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
    except Exception as e:
        print(f"Error updating position: {e}")


def get_alpaca_headers(env):
    """Get Alpaca API authentication headers"""
    return Headers.new({
        "APCA-API-KEY-ID": env.ALPACA_API_KEY,
        "APCA-API-SECRET-KEY": env.ALPACA_SECRET_KEY,
        "Content-Type": "application/json"
    }.items())
