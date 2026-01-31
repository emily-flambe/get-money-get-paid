import asyncio
import logging
from typing import Optional

from .websocket import AlpacaWebSocket
from .indicators import TickBuffer
from .orders import OrderManager
from .strategies import Strategy, Signal, SignalType

log = logging.getLogger(__name__)


class TradingEngine:
    """
    Core trading engine - connects WebSocket to strategies to order execution.
    """

    def __init__(
        self,
        websocket: AlpacaWebSocket,
        order_manager: OrderManager,
        strategies: list[Strategy],
        tick_buffer: Optional[TickBuffer] = None,
    ):
        self.ws = websocket
        self.orders = order_manager
        self.strategies = strategies
        self.tick_buffer = tick_buffer or TickBuffer()

        # Build symbol -> strategies mapping
        self.symbol_strategies: dict[str, list[Strategy]] = {}
        for strategy in strategies:
            for symbol in strategy.symbols:
                if symbol not in self.symbol_strategies:
                    self.symbol_strategies[symbol] = []
                self.symbol_strategies[symbol].append(strategy)

        # Stats
        self.tick_count = 0
        self.signal_count = 0
        self.order_count = 0

        # Wire up callbacks
        self.ws.on_trade = self.on_trade
        self.ws.on_bar = self.on_bar

    @property
    def symbols(self) -> list[str]:
        """All symbols we need to subscribe to"""
        return list(self.symbol_strategies.keys())

    async def on_trade(self, symbol: str, price: float, size: int, timestamp: str):
        """Handle incoming trade tick"""
        self.tick_count += 1

        # Update tick buffer
        self.tick_buffer.add(symbol, price, size)

        # Get indicators for this symbol
        indicators = self.tick_buffer.get_indicators(symbol)

        # Run strategies for this symbol
        if symbol in self.symbol_strategies:
            for strategy in self.symbol_strategies[symbol]:
                if not strategy.enabled:
                    continue

                try:
                    signal = strategy.on_tick(symbol, price, indicators)
                    if signal:
                        await self.handle_signal(signal, strategy)
                except Exception as e:
                    log.error(f"Strategy {strategy.name} error on tick: {e}")

    async def on_bar(self, symbol: str, bar: dict):
        """Handle incoming 1-minute bar"""
        indicators = self.tick_buffer.get_indicators(symbol)

        if symbol in self.symbol_strategies:
            for strategy in self.symbol_strategies[symbol]:
                if not strategy.enabled:
                    continue

                try:
                    signal = strategy.on_bar(symbol, bar, indicators)
                    if signal:
                        await self.handle_signal(signal, strategy)
                except Exception as e:
                    log.error(f"Strategy {strategy.name} error on bar: {e}")

    async def handle_signal(self, signal: Signal, strategy: Strategy):
        """Process a signal from a strategy"""
        self.signal_count += 1
        log.info(f"Signal: {signal.strategy_name} - {signal.type.value} {signal.symbol} @ ${signal.price:.2f} ({signal.reason})")

        # Calculate dollar amount
        if signal.type == SignalType.BUY:
            dollar_amount = strategy.cash_allocation * strategy.position_size_pct
        else:
            dollar_amount = 0  # Sells use quantity, not notional

        # Submit order
        order = await self.orders.submit(signal, dollar_amount)

        if order:
            self.order_count += 1

            # Update strategy position tracking
            if signal.type == SignalType.BUY:
                filled_qty = float(order.get("filled_qty", 0)) or (dollar_amount / signal.price)
                strategy.update_position(signal.symbol, strategy.get_position(signal.symbol) + filled_qty)
            else:
                strategy.update_position(signal.symbol, 0)

    async def run(self):
        """Main run loop"""
        log.info(f"Starting trading engine with {len(self.strategies)} strategies")
        log.info(f"Symbols: {self.symbols}")

        # Connect and authenticate
        await self.ws.connect()

        # Subscribe to data
        await self.ws.subscribe(trades=self.symbols, bars=self.symbols)

        # Refresh account data
        await self.orders.refresh_account()

        # Start periodic account refresh
        asyncio.create_task(self._account_refresh_loop())

        # Start stats logging
        asyncio.create_task(self._stats_loop())

        # Run WebSocket loop
        await self.ws.run()

    async def _account_refresh_loop(self):
        """Periodically refresh account data"""
        while self.ws.running:
            await asyncio.sleep(60)
            await self.orders.refresh_account()

    async def _stats_loop(self):
        """Log stats periodically"""
        while self.ws.running:
            await asyncio.sleep(30)
            log.info(f"Stats: {self.tick_count} ticks, {self.signal_count} signals, {self.order_count} orders")

    async def stop(self):
        """Stop the engine"""
        await self.ws.close()
        await self.orders.close()
