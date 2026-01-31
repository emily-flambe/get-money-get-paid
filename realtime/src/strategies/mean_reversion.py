from typing import Optional
from .base import Strategy, Signal, SignalType


class MeanReversionStrategy(Strategy):
    """
    Mean reversion strategy - buy when price drops below mean, sell when it recovers.

    Params:
        window_seconds: Rolling window for mean/std calculation
        std_threshold: Number of std devs below mean to trigger buy
        exit_threshold: Std devs from mean to trigger exit (closer to 0)
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.window_seconds = self.params.get("window_seconds", 60)
        self.std_threshold = self.params.get("std_threshold", 2.0)
        self.exit_threshold = self.params.get("exit_threshold", 0.5)

    def on_tick(self, symbol: str, price: float, indicators: dict) -> Optional[Signal]:
        # Get rolling stats from indicators
        mean = indicators.get(f"mean_{self.window_seconds}s")
        std = indicators.get(f"std_{self.window_seconds}s")

        if mean is None or std is None or std == 0:
            return None

        if self.in_cooldown(symbol):
            return None

        # Calculate z-score (how many std devs from mean)
        z_score = (price - mean) / std

        # Entry: price significantly below mean
        if z_score < -self.std_threshold and not self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.BUY,
                symbol,
                price,
                f"Oversold: z={z_score:.2f} < -{self.std_threshold}"
            )

        # Exit: price recovered back toward mean
        if abs(z_score) < self.exit_threshold and self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.SELL,
                symbol,
                price,
                f"Reverted: z={z_score:.2f} within {self.exit_threshold} of mean"
            )

        # Also exit if price goes too high (take profit)
        if z_score > self.std_threshold and self.has_position(symbol):
            self.record_signal(symbol)
            return self._make_signal(
                SignalType.SELL,
                symbol,
                price,
                f"Take profit: z={z_score:.2f} > {self.std_threshold}"
            )

        return None
