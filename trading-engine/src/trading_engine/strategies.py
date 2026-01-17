"""
Pure strategy logic functions that can be tested without Cloudflare dependencies.
"""


def calculate_rsi(bars, period):
    """
    Calculate RSI (Relative Strength Index) from price bars.

    Args:
        bars: List of OHLCV bars with 'c' (close) prices
        period: RSI period (typically 14)

    Returns:
        RSI value between 0 and 100
    """
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


def calculate_sma(prices, period):
    """
    Calculate Simple Moving Average.

    Args:
        prices: List of prices
        period: SMA period

    Returns:
        SMA value
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_momentum(start_price, end_price):
    """
    Calculate momentum as percentage change.

    Args:
        start_price: Starting price
        end_price: Ending price

    Returns:
        Momentum as percentage
    """
    if start_price == 0:
        return 0
    return ((end_price - start_price) / start_price) * 100


def should_buy_sma_crossover(short_sma, long_sma, has_position):
    """
    Determine if SMA crossover strategy should buy.

    Args:
        short_sma: Short-term SMA value
        long_sma: Long-term SMA value
        has_position: Whether we already have a position

    Returns:
        True if should buy, False otherwise
    """
    return short_sma > long_sma and not has_position


def should_sell_sma_crossover(short_sma, long_sma, has_position):
    """
    Determine if SMA crossover strategy should sell.

    Args:
        short_sma: Short-term SMA value
        long_sma: Long-term SMA value
        has_position: Whether we have a position to sell

    Returns:
        True if should sell, False otherwise
    """
    return short_sma < long_sma and has_position


def should_buy_rsi(rsi, oversold_threshold, has_position):
    """
    Determine if RSI strategy should buy.

    Args:
        rsi: Current RSI value
        oversold_threshold: RSI level considered oversold (typically 30)
        has_position: Whether we already have a position

    Returns:
        True if should buy, False otherwise
    """
    return rsi < oversold_threshold and not has_position


def should_sell_rsi(rsi, overbought_threshold, has_position):
    """
    Determine if RSI strategy should sell.

    Args:
        rsi: Current RSI value
        overbought_threshold: RSI level considered overbought (typically 70)
        has_position: Whether we have a position to sell

    Returns:
        True if should sell, False otherwise
    """
    return rsi > overbought_threshold and has_position


def should_buy_momentum(momentum_pct, threshold_pct, has_position):
    """
    Determine if momentum strategy should buy.

    Args:
        momentum_pct: Momentum as percentage
        threshold_pct: Threshold percentage for triggering trades
        has_position: Whether we already have a position

    Returns:
        True if should buy, False otherwise
    """
    return momentum_pct > threshold_pct and not has_position


def should_sell_momentum(momentum_pct, threshold_pct, has_position):
    """
    Determine if momentum strategy should sell.

    Args:
        momentum_pct: Momentum as percentage
        threshold_pct: Threshold percentage for triggering trades
        has_position: Whether we have a position to sell

    Returns:
        True if should sell, False otherwise
    """
    return momentum_pct < -threshold_pct and has_position
