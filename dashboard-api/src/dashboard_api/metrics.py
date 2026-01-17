"""
Performance metrics calculation functions.
Pure functions that can be tested without Cloudflare dependencies.
"""


def calculate_total_return(initial_equity, final_equity):
    """
    Calculate total return as a percentage.

    Args:
        initial_equity: Starting equity value
        final_equity: Ending equity value

    Returns:
        Total return as percentage (e.g., 10.0 for 10%)
    """
    if initial_equity <= 0:
        return 0
    return ((final_equity - initial_equity) / initial_equity) * 100


def calculate_daily_returns(snapshots):
    """
    Calculate daily returns from equity snapshots.

    Args:
        snapshots: List of snapshot dicts with 'equity' key

    Returns:
        List of daily returns as decimals
    """
    if len(snapshots) < 2:
        return []

    daily_returns = []
    for i in range(1, len(snapshots)):
        prev_equity = snapshots[i-1]["equity"]
        curr_equity = snapshots[i]["equity"]
        if prev_equity > 0:
            daily_returns.append((curr_equity - prev_equity) / prev_equity)
    return daily_returns


def calculate_sharpe_ratio(daily_returns, annualization_factor=252):
    """
    Calculate annualized Sharpe ratio from daily returns.

    Args:
        daily_returns: List of daily returns as decimals
        annualization_factor: Trading days per year (default 252)

    Returns:
        Annualized Sharpe ratio
    """
    if not daily_returns:
        return 0

    avg_return = sum(daily_returns) / len(daily_returns)
    variance = sum((r - avg_return) ** 2 for r in daily_returns) / len(daily_returns)
    std_return = variance ** 0.5

    if std_return == 0:
        return 0

    return (avg_return / std_return) * (annualization_factor ** 0.5)


def calculate_max_drawdown(snapshots):
    """
    Calculate maximum drawdown from equity snapshots.

    Args:
        snapshots: List of snapshot dicts with 'equity' key

    Returns:
        Maximum drawdown as decimal (e.g., 0.10 for 10% drawdown)
    """
    if not snapshots:
        return 0

    peak = snapshots[0]["equity"]
    max_drawdown = 0

    for snap in snapshots:
        equity = snap["equity"]
        if equity > peak:
            peak = equity
        if peak > 0:
            drawdown = (peak - equity) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown

    return max_drawdown


def calculate_win_rate(trades):
    """
    Calculate win rate from trades.

    Args:
        trades: List of trade dicts with 'pnl' key

    Returns:
        Win rate as decimal (e.g., 0.60 for 60%)
    """
    if not trades:
        return 0

    winning_trades = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return winning_trades / len(trades)
