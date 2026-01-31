from .base import Strategy, Signal, SignalType
from .momentum import MomentumStrategy
from .mean_reversion import MeanReversionStrategy
from .buy_and_hold import BuyAndHoldStrategy
from .sma_crossover import SMACrossoverStrategy
from .rsi import RSIStrategy

STRATEGY_TYPES = {
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
    "buy_and_hold": BuyAndHoldStrategy,
    "sma_crossover": SMACrossoverStrategy,
    "rsi": RSIStrategy,
}

def create_strategy(config: dict) -> Strategy:
    """Factory function to create strategy from config"""
    strategy_type = config["type"]
    if strategy_type not in STRATEGY_TYPES:
        raise ValueError(f"Unknown strategy type: {strategy_type}")
    return STRATEGY_TYPES[strategy_type](config)

__all__ = ["Strategy", "Signal", "SignalType", "create_strategy", "STRATEGY_TYPES"]
