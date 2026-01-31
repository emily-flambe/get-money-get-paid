from typing import Optional
from .base import Strategy, Signal, SignalType


class MomentumStrategy(Strategy):
    """
    Momentum strategy - buy on quick price increases, sell on reversals.

    Params:
        threshold_pct: Minimum % move to trigger buy (e.g., 0.05 = 0.05%)
        exit_threshold_pct: % reversal to trigger exit
        lookback_seconds: Window to measure momentum over
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.threshold_pct = self.params.get("threshold_pct", 0.05)
        self.exit_threshold_pct = self.params.get("exit_threshold_pct", 0.03)
        self.lookback_seconds = self.params.get("lookback_seconds", 10)

    def on_tick(self, symbol: str, price: float, indicators: dict) -> Optional[Signal]:
        # Get momentum from indicators (computed by TickBuffer)
        momentum_key = f"momentum_{self.lookback_seconds}s"
        momentum = indicators.get(momentum_key)

        if momentum is None:
            # Not enough data yet
            return None

        if self.in_cooldown(symbol):
            return None

        # Entry: momentum exceeds threshold and no position
        if momentum > self.threshold_pct and not self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.BUY,
                symbol,
                price,
                f"Momentum {momentum:.3f}% > {self.threshold_pct}%"
            )

        # Exit: negative momentum exceeds exit threshold and has position
        if momentum < -self.exit_threshold_pct and self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.SELL,
                symbol,
                price,
                f"Reversal {momentum:.3f}% < -{self.exit_threshold_pct}%"
            )

        return None
