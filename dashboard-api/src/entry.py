"""
Dashboard API Worker
REST API for the paper trading dashboard frontend.
"""
from js import fetch, Response, Headers, JSON
import json
import uuid


async def on_fetch(request, env, ctx):
    """Main request handler"""
    url = request.url
    method = request.method

    # Parse path
    path = url.split("://")[1].split("/", 1)[1] if "://" in url else url
    path = "/" + path.split("?")[0] if path else "/"

    # CORS headers
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
        # Route handling
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

        elif path == "/api/comparison" or path == "api/comparison":
            return await get_comparison(env, cors_headers)

        elif path == "/api/account" or path == "api/account":
            return await get_account(env, cors_headers)

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


async def list_algorithms(env, cors_headers):
    """GET /api/algorithms - List all algorithms"""
    result = await env.DB.prepare("SELECT * FROM algorithms ORDER BY created_at DESC").all()

    algorithms = []
    for row in result.results:
        algo = dict(row)
        algo["config"] = json.loads(algo["config"]) if isinstance(algo["config"], str) else algo["config"]
        algo["symbols"] = json.loads(algo["symbols"]) if isinstance(algo["symbols"], str) else algo["symbols"]
        algorithms.append(algo)

    return Response.new(
        json.dumps({"algorithms": algorithms}),
        headers=Headers.new(cors_headers.items())
    )


async def create_algorithm(data, env, cors_headers):
    """POST /api/algorithms - Create new algorithm"""
    algo_id = str(uuid.uuid4())

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

    return Response.new(
        json.dumps({"id": algo_id, "message": "Algorithm created"}),
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

    algo = dict(result)
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

    return Response.new(
        json.dumps({"trades": [dict(row) for row in result.results]}),
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm_snapshots(algo_id, env, cors_headers):
    """GET /api/algorithms/{id}/snapshots - Get snapshots for algorithm"""
    result = await env.DB.prepare("""
        SELECT * FROM snapshots WHERE algorithm_id = ? ORDER BY snapshot_date ASC
    """).bind(algo_id).all()

    snapshots = []
    for row in result.results:
        snap = dict(row)
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

    return Response.new(
        json.dumps({"positions": [dict(row) for row in result.results]}),
        headers=Headers.new(cors_headers.items())
    )


async def get_algorithm_performance(algo_id, env, cors_headers):
    """GET /api/algorithms/{id}/performance - Calculate performance metrics"""
    snapshots = await env.DB.prepare("""
        SELECT * FROM snapshots WHERE algorithm_id = ? ORDER BY snapshot_date ASC
    """).bind(algo_id).all()

    if not snapshots.results:
        return Response.new(
            json.dumps({
                "algorithm_id": algo_id,
                "initial_equity": 0,
                "final_equity": 0,
                "total_return_pct": 0,
                "sharpe_ratio": 0,
                "max_drawdown_pct": 0,
                "total_trades": 0,
                "days_active": 0
            }),
            headers=Headers.new(cors_headers.items())
        )

    snapshots_list = [dict(s) for s in snapshots.results]

    initial_equity = snapshots_list[0]["equity"]
    final_equity = snapshots_list[-1]["equity"]
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
    trade_count = trades["count"] if trades else 0

    return Response.new(
        json.dumps({
            "algorithm_id": algo_id,
            "initial_equity": round(initial_equity, 2),
            "final_equity": round(final_equity, 2),
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
    for algo in algorithms.results:
        algo_dict = dict(algo)
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
        headers = Headers.new({
            "APCA-API-KEY-ID": env.ALPACA_API_KEY,
            "APCA-API-SECRET-KEY": env.ALPACA_SECRET_KEY
        }.items())

        response = await fetch(
            "https://paper-api.alpaca.markets/v2/account",
            {"method": "GET", "headers": headers}
        )
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
