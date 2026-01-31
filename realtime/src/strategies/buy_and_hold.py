from typing import Optional
from .base import Strategy, Signal, SignalType


class BuyAndHoldStrategy(Strategy):
    """
    Buy and hold strategy - buy once and hold forever.

    Used as a benchmark to compare other strategies against.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.bought = set()  # Track which symbols we've bought

    def on_tick(self, symbol: str, price: float, indicators: dict) -> Optional[Signal]:
        # Only buy once per symbol
        if symbol in self.bought:
            return None

        if not self.has_position(symbol):
            self.bought.add(symbol)
            return self._make_signal(
                SignalType.BUY,
                symbol,
                price,
                "Buy and hold initial purchase"
            )

        return None

    def on_bar(self, symbol: str, bar: dict, indicators: dict) -> Optional[Signal]:
        # Also check on bar close in case we missed the tick
        return self.on_tick(symbol, bar["close"], indicators)
