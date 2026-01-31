"""
Dashboard API Worker
REST API for the paper trading dashboard frontend.
Serves both static frontend assets and API endpoints.
"""
from js import fetch, Response, Headers, JSON, Request
import json
import uuid
import datetime
from static_assets import INDEX_HTML, STYLES_CSS, API_JS, CHARTS_JS, APP_JS


async def on_fetch(request, env, ctx):
    """Main request handler"""
    url = request.url
    method = request.method

    # Parse path
    path = url.split("://")[1].split("/", 1)[1] if "://" in url else url
    path = "/" + path.split("?")[0] if path else "/"

    # CORS headers for API
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }

    # Handle preflight
    if method == "OPTIONS":
        return Response.new("", headers=Headers.new(cors_headers.items()))

    try:
        # Static file serving
        if path == "/" or path == "" or path == "/index.html":
            return Response.new(
                INDEX_HTML,
                headers=Headers.new({"Content-Type": "text/html; charset=utf-8"}.items())
            )

        if path == "/css/styles.css":
            return Response.new(
                STYLES_CSS,
                headers=Headers.new({"Content-Type": "text/css; charset=utf-8"}.items())
            )

        if path == "/js/api.js":
            return Response.new(
                API_JS,
                headers=Headers.new({"Content-Type": "application/javascript; charset=utf-8"}.items())
            )

        if path == "/js/charts.js":
            return Response.new(
                CHARTS_JS,
                headers=Headers.new({"Content-Type": "application/javascript; charset=utf-8"}.items())
            )

        if path == "/js/app.js":
            return Response.new(
                APP_JS,
                headers=Headers.new({"Content-Type": "application/javascript; charset=utf-8"}.items())
            )

        # API Route handling
        if path == "/api/algorithms" or path == "api/algorithms":
            if method == "GET":
                return await list_algorithms(env, cors_headers)
            elif method == "POST":
                body = await request.text()
                return await create_algorithm(json.loads(body), env, cors_headers)

        elif path.startswith("/api/algorithms/") or path.startswith("api/algorithms/"):
            parts = path.replace("/api/algorithms/", "").replace("api/algorithms/", "").split("/")
            algo_id = parts[0]

            if len(parts) == 1:
                if method == "GET":
                    return await get_algorithm(algo_id, env, cors_headers)
                elif method == "PUT":
                    body = await request.text()
                    return await update_algorithm(algo_id, json.loads(body), env, cors_headers)
                elif method == "DELETE":
                    return await delete_algorithm(algo_id, env, cors_headers)

            elif len(parts) == 2:
                sub_resource = parts[1]
                if sub_resource == "trades":
                    return await get_algorithm_trades(algo_id, env, cors_headers)
                elif sub_resource == "snapshots":
                    return await get_algorithm_snapshots(algo_id, env, cors_headers)
                elif sub_resource == "positions":
                    return await get_algorithm_positions(algo_id, env, cors_headers)
                elif sub_resource == "performance":
                    return await get_algorithm_performance(algo_id, env, cors_headers)

        elif path == "/api/trades" or path == "api/trades":
            if method == "POST":
                body = await request.text()
                return await create_trade(json.loads(body), env, cors_headers)

        elif path == "/api/comparison" or path == "api/comparison":
            return await get_comparison(env, cors_headers)

        elif path == "/api/account" or path == "api/account":
            return await get_account(env, cors_headers)

        elif path == "/api/settings" or path == "api/settings":
            return await get_settings(env, cors_headers)

        elif path == "/health" or path == "health":
            return Response.new(
                json.dumps({"status": "ok"}),
                headers=Headers.new(cors_headers.items())
            )

        # 404
        return Response.new(
            json.dumps({"error": "Not found", "path": path}),
            status=404,
            headers=Headers.new(cors_headers.items())
        )

    except Exception as e:
        return Response.new(
            json.dumps({"error": str(e)}),
            status=500,
            headers=Headers.new(cors_headers.items())
        )


def js_to_py(obj):
    """Convert JsProxy object to Python dict/list"""
    if hasattr(obj, 'to_py'):
        return obj.to_py()
    return obj


async def list_algorithms(env, cors_headers):
    """GET /api/algorithms - List all algorithms"""
    result = await env.DB.prepare("SELECT * FROM algorithms ORDER BY created_at DESC").all()

    algorithms = []
    results = js_to_py(result.results)
    for row in results:
        algo = js_to_py(row) if hasattr(row, 'to_py') else dict(row)
        algo["config"] = json.loads(algo["config"]) if isinstance(algo["config"], str) else algo["config"]
        algo["symbols"] = json.loads(algo["symbols"]) if isinstance(algo["symbols"], str) else algo["symbols"]

        # Get latest snapshot cash for this algorithm
        latest_snapshot = await env.DB.prepare("""
            SELECT cash FROM snapshots WHERE algorithm_id = ? ORDER BY snapshot_date DESC LIMIT 1
        """).bind(algo["id"]).first()
        if latest_snapshot:
            snap_data = js_to_py(latest_snapshot) if hasattr(latest_snapshot, 'to_py') else dict(latest_snapshot)
            algo["cash"] = snap_data.get("cash", 0)
        else:
            algo["cash"] = 0

        algorithms.append(algo)

    return Response.new(
        json.dumps({"algorithms": algorithms}),
        headers=Headers.new(cors_headers.items())
    )


async def create_algorithm(data, env, cors_headers):
    """POST /api/algorithms - Create new algorithm"""
    algo_id = str(uuid.uuid4())

    # Get default starting balance from system_state (default 1000 if not set)
    starting_balance_result = await env.DB.prepare("""
        SELECT value FROM system_state WHERE key = 'default_starting_balance'
    """).first()
    if starting_balance_result:
        sb_data = js_to_py(starting_balance_result) if hasattr(starting_balance_result, 'to_py') else dict(starting_balance_result)
        starting_balance = float(sb_data.get("value", 1000))
    else:
        starting_balance = 1000.0

    await env.DB.prepare("""
        INSERT INTO algorithms (id, name, description, strategy_type, config, symbols, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """).bind(
        algo_id,
        data.get("name", "Unnamed"),
        data.get("description", ""),
        data.get("strategy_type", "sma_crossover"),
        json.dumps(data.get("config", {})),
        json.dumps(data.get("symbols", [])),
        1 if data.get("enabled", True) else 0
    ).run()

    # Create initial snapshot with starting balance
    snapshot_id = str(uuid.uuid4())
    snapshot_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    await env.DB.prepare("""
        INSERT INTO snapshots (id, algorithm_id, snapshot_date, equity, cash, positions)
        VALUES (?, ?, ?, ?, ?, ?)
    """).bind(
        snapshot_id,
        algo_id,
        snapshot_date,
        starting_balance,
        starting_balance,
        json.dumps([])
    ).run()

    return Response.new(
        json.dumps({"id": algo_id, "message": "Algorithm created", "starting_balance": starting_balance}),
        status=201,
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm(algo_id, env, cors_headers):
    """GET /api/algorithms/{id} - Get algorithm details"""
    result = await env.DB.prepare(
        "SELECT * FROM algorithms WHERE id = ?"
    ).bind(algo_id).first()

    if not result:
        return Response.new(
            json.dumps({"error": "Algorithm not found"}),
            status=404,
            headers=Headers.new(cors_headers.items())
        )

    algo = js_to_py(result) if hasattr(result, 'to_py') else dict(result)
    algo["config"] = json.loads(algo["config"]) if isinstance(algo["config"], str) else algo["config"]
    algo["symbols"] = json.loads(algo["symbols"]) if isinstance(algo["symbols"], str) else algo["symbols"]

    return Response.new(
        json.dumps(algo),
        headers=Headers.new(cors_headers.items())
    )


async def update_algorithm(algo_id, data, env, cors_headers):
    """PUT /api/algorithms/{id} - Update algorithm"""
    updates = []
    binds = []

    if "name" in data:
        updates.append("name = ?")
        binds.append(data["name"])
    if "description" in data:
        updates.append("description = ?")
        binds.append(data["description"])
    if "config" in data:
        updates.append("config = ?")
        binds.append(json.dumps(data["config"]))
    if "symbols" in data:
        updates.append("symbols = ?")
        binds.append(json.dumps(data["symbols"]))
    if "enabled" in data:
        updates.append("enabled = ?")
        binds.append(1 if data["enabled"] else 0)

    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        binds.append(algo_id)
        query = f"UPDATE algorithms SET {', '.join(updates)} WHERE id = ?"
        await env.DB.prepare(query).bind(*binds).run()

    return Response.new(
        json.dumps({"message": "Algorithm updated"}),
        headers=Headers.new(cors_headers.items())
    )


async def delete_algorithm(algo_id, env, cors_headers):
    """DELETE /api/algorithms/{id} - Delete algorithm"""
    await env.DB.prepare("DELETE FROM algorithms WHERE id = ?").bind(algo_id).run()
    await env.DB.prepare("DELETE FROM trades WHERE algorithm_id = ?").bind(algo_id).run()
    await env.DB.prepare("DELETE FROM positions WHERE algorithm_id = ?").bind(algo_id).run()
    await env.DB.prepare("DELETE FROM snapshots WHERE algorithm_id = ?").bind(algo_id).run()

    return Response.new(
        json.dumps({"message": "Algorithm deleted"}),
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm_trades(algo_id, env, cors_headers):
    """GET /api/algorithms/{id}/trades - Get trades for algorithm"""
    result = await env.DB.prepare("""
        SELECT * FROM trades WHERE algorithm_id = ? ORDER BY submitted_at DESC LIMIT 100
    """).bind(algo_id).all()

    results = js_to_py(result.results)
    trades = [js_to_py(row) if hasattr(row, 'to_py') else dict(row) for row in results]

    return Response.new(
        json.dumps({"trades": trades}),
        headers=Headers.new(cors_headers.items())
    )


async def create_trade(data, env, cors_headers):
    """POST /api/trades - Record a trade from the realtime engine"""
    trade_id = data.get("id") or str(uuid.uuid4())

    await env.DB.prepare("""
        INSERT INTO trades (id, algorithm_id, symbol, side, quantity, order_type, status, alpaca_order_id, notes, filled_price, filled_qty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """).bind(
        trade_id,
        data.get("algorithm_id"),
        data.get("symbol"),
        data.get("side"),
        data.get("quantity", 0),
        data.get("order_type", "market"),
        data.get("status", "filled"),
        data.get("alpaca_order_id", ""),
        data.get("notes", ""),
        data.get("filled_price", 0),
        data.get("filled_qty", 0)
    ).run()

    return Response.new(
        json.dumps({"id": trade_id, "message": "Trade recorded"}),
        status=201,
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm_snapshots(algo_id, env, cors_headers):
    """GET /api/algorithms/{id}/snapshots - Get snapshots for algorithm"""
    result = await env.DB.prepare("""
        SELECT * FROM snapshots WHERE algorithm_id = ? ORDER BY snapshot_date ASC
    """).bind(algo_id).all()

    snapshots = []
    results = js_to_py(result.results)
    for row in results:
        snap = js_to_py(row) if hasattr(row, 'to_py') else dict(row)
        snap["positions"] = json.loads(snap["positions"]) if snap.get("positions") and isinstance(snap["positions"], str) else snap.get("positions")
        snapshots.append(snap)

    return Response.new(
        json.dumps({"snapshots": snapshots}),
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm_positions(algo_id, env, cors_headers):
    """GET /api/algorithms/{id}/positions - Get current positions"""
    result = await env.DB.prepare("""
        SELECT * FROM positions WHERE algorithm_id = ?
    """).bind(algo_id).all()

    results = js_to_py(result.results)
    positions = [js_to_py(row) if hasattr(row, 'to_py') else dict(row) for row in results]

    return Response.new(
        json.dumps({"positions": positions}),
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm_performance(algo_id, env, cors_headers):
    """GET /api/algorithms/{id}/performance - Calculate performance metrics"""
    snapshots = await env.DB.prepare("""
        SELECT * FROM snapshots WHERE algorithm_id = ? ORDER BY snapshot_date ASC
    """).bind(algo_id).all()

    results = js_to_py(snapshots.results)
    if not results:
        return Response.new(
            json.dumps({
                "algorithm_id": algo_id,
                "initial_equity": 0,
                "final_equity": 0,
                "current_cash": 0,
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
                "total_trades": 0,
                "days_active": 0
            }),
            headers=Headers.new(cors_headers.items())
        )

    snapshots_list = [js_to_py(s) if hasattr(s, 'to_py') else dict(s) for s in results]

    initial_equity = snapshots_list[0]["equity"]
    initial_cash = snapshots_list[0].get("cash", initial_equity)

    # Get current cash from latest snapshot
    latest_snap = snapshots_list[-1]
    current_cash = latest_snap.get("cash", 0)

    # Get current positions and calculate total position market value
    positions_result = await env.DB.prepare("""
        SELECT quantity, avg_entry_price, market_value FROM positions WHERE algorithm_id = ?
    """).bind(algo_id).all()
    positions_list = js_to_py(positions_result.results)
    total_position_value = 0
    for pos in positions_list:
        pos_dict = js_to_py(pos) if hasattr(pos, 'to_py') else dict(pos)
        # Use market_value if set, otherwise calculate from quantity * avg_entry_price
        market_val = pos_dict.get("market_value")
        if market_val is None or market_val == 0:
            qty = pos_dict.get("quantity") or 0
            price = pos_dict.get("avg_entry_price") or 0
            market_val = qty * price
        total_position_value += market_val

    # Calculate current equity = cash + sum of position market values
    final_equity = current_cash + total_position_value

    total_return = ((final_equity - initial_equity) / initial_equity * 100) if initial_equity > 0 else 0

    # Daily returns for Sharpe ratio
    daily_returns = []
    for i in range(1, len(snapshots_list)):
        prev_equity = snapshots_list[i-1]["equity"]
        curr_equity = snapshots_list[i]["equity"]
        if prev_equity > 0:
            daily_returns.append((curr_equity - prev_equity) / prev_equity)

    # Sharpe ratio (annualized, 252 trading days)
    sharpe_ratio = 0
    if daily_returns:
        avg_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
        std_return = variance ** 0.5
        if std_return > 0:
            sharpe_ratio = (avg_return / std_return) * (252 ** 0.5)

    # Max drawdown
    peak = snapshots_list[0]["equity"]
    max_drawdown = 0
    for snap in snapshots_list:
        if snap["equity"] > peak:
            peak = snap["equity"]
        if peak > 0:
            drawdown = (peak - snap["equity"]) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    # Trade count
    trades = await env.DB.prepare("""
        SELECT COUNT(*) as count FROM trades WHERE algorithm_id = ?
    """).bind(algo_id).first()
    trades_dict = js_to_py(trades) if trades and hasattr(trades, 'to_py') else (dict(trades) if trades else {})
    trade_count = trades_dict.get("count", 0) if trades_dict else 0

    return Response.new(
        json.dumps({
            "algorithm_id": algo_id,
            "initial_equity": round(initial_equity, 2),
            "final_equity": round(final_equity, 2),
            "current_cash": round(current_cash, 2),
            "total_return_pct": round(total_return, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown_pct": round(max_drawdown * 100, 2),
            "total_trades": trade_count,
            "days_active": len(snapshots_list)
        }),
        headers=Headers.new(cors_headers.items())
    )


async def get_comparison(env, cors_headers):
    """GET /api/comparison - Compare all algorithms"""
    algorithms = await env.DB.prepare("SELECT id, name FROM algorithms").all()

    comparison = []
    results = js_to_py(algorithms.results)
    for algo in results:
        algo_dict = js_to_py(algo) if hasattr(algo, 'to_py') else dict(algo)
        # Get performance for each
        perf_response = await get_algorithm_performance(algo_dict["id"], env, cors_headers)
        perf_text = await perf_response.text()
        perf = json.loads(perf_text)
        perf["name"] = algo_dict["name"]
        comparison.append(perf)

    # Sort by total return
    comparison.sort(key=lambda x: x.get("total_return_pct", 0), reverse=True)

    return Response.new(
        json.dumps({"comparison": comparison}),
        headers=Headers.new(cors_headers.items())
    )


async def get_account(env, cors_headers):
    """GET /api/account - Get Alpaca account info"""
    try:
        headers = Headers.new()
        headers.set("APCA-API-KEY-ID", str(env.ALPACA_API_KEY))
        headers.set("APCA-API-SECRET-KEY", str(env.ALPACA_SECRET_KEY))
        headers.set("Content-Type", "application/json")

        init = JSON.parse(json.dumps({"method": "GET"}))
        init.headers = headers

        request = Request.new("https://paper-api.alpaca.markets/v2/account", init)
        response = await fetch(request)
        data = json.loads(await response.text())

        return Response.new(
            json.dumps(data),
            headers=Headers.new(cors_headers.items())
        )
    except Exception as e:
        return Response.new(
            json.dumps({"error": str(e)}),
            status=500,
            headers=Headers.new(cors_headers.items())
        )


async def get_settings(env, cors_headers):
    """GET /api/settings - Get system settings"""
    # Get default starting balance from system_state
    starting_balance_result = await env.DB.prepare("""
        SELECT value FROM system_state WHERE key = 'default_starting_balance'
    """).first()

    if starting_balance_result:
        sb_data = js_to_py(starting_balance_result) if hasattr(starting_balance_result, 'to_py') else dict(starting_balance_result)
        default_starting_balance = float(sb_data.get("value", 1000))
    else:
        default_starting_balance = 1000.0

    return Response.new(
        json.dumps({
            "default_starting_balance": default_starting_balance
        }),
        headers=Headers.new(cors_headers.items())
    )
