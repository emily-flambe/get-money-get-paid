from typing import Optional
from .base import Strategy, Signal, SignalType


class SMACrossoverStrategy(Strategy):
    """
    SMA Crossover strategy - buy when short SMA crosses above long SMA.

    This is a trend-following strategy that aims to capture momentum
    when shorter-term price averages overtake longer-term averages.

    For real-time trading, we approximate SMAs using rolling means
    from the tick buffer (e.g., 30s mean vs 120s mean as proxies).

    Params:
        short_window_seconds: Window for short SMA (default 30s)
        long_window_seconds: Window for long SMA (default 120s)
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.short_window = self.params.get("short_window_seconds", 30)
        self.long_window = self.params.get("long_window_seconds", 120)

        # Track previous crossover state to detect crosses
        self.prev_short_above: dict[str, Optional[bool]] = {}

    def on_tick(self, symbol: str, price: float, indicators: dict) -> Optional[Signal]:
        short_key = f"mean_{self.short_window}s"
        long_key = f"mean_{self.long_window}s"

        short_sma = indicators.get(short_key)
        long_sma = indicators.get(long_key)

        if short_sma is None or long_sma is None:
            return None

        if self.in_cooldown(symbol):
            return None

        short_above = short_sma > long_sma
        prev_state = self.prev_short_above.get(symbol)
        self.prev_short_above[symbol] = short_above

        # Need previous state to detect crossover
        if prev_state is None:
            return None

        # Bullish crossover: short crosses above long
        if short_above and not prev_state and not self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.BUY,
                symbol,
                price,
                f"SMA crossover: {short_sma:.2f} > {long_sma:.2f}"
            )

        # Bearish crossover: short crosses below long
        if not short_above and prev_state and self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.SELL,
                symbol,
                price,
                f"SMA crossunder: {short_sma:.2f} < {long_sma:.2f}"
            )

        return None
