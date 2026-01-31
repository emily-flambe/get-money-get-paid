import asyncio
import logging
from typing import Callable, Optional
import websockets
import orjson

log = logging.getLogger(__name__)


class AlpacaWebSocket:
    """
    WebSocket client for Alpaca real-time market data.

    Connects to the IEX feed (free) and streams trades and bars.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        data_url: str = "wss://stream.data.alpaca.markets/v2/iex",
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.data_url = data_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False

        # Callbacks
        self.on_trade: Optional[Callable] = None
        self.on_bar: Optional[Callable] = None
        self.on_quote: Optional[Callable] = None

    async def connect(self):
        """Establish WebSocket connection and authenticate"""
        log.info(f"Connecting to {self.data_url}")
        self.ws = await websockets.connect(self.data_url)

        # Wait for welcome message
        msg = await self.ws.recv()
        data = orjson.loads(msg)
        log.info(f"Connected: {data}")

        # Authenticate
        auth_msg = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.secret_key,
        }
        await self.ws.send(orjson.dumps(auth_msg))

        msg = await self.ws.recv()
        data = orjson.loads(msg)
        if data[0].get("msg") == "authenticated":
            log.info("Authenticated successfully")
        else:
            raise Exception(f"Authentication failed: {data}")

    async def subscribe(self, trades: list[str] = None, bars: list[str] = None, quotes: list[str] = None):
        """Subscribe to market data streams"""
        sub_msg = {"action": "subscribe"}

        if trades:
            sub_msg["trades"] = trades
        if bars:
            sub_msg["bars"] = bars
        if quotes:
            sub_msg["quotes"] = quotes

        log.info(f"Subscribing: {sub_msg}")
        await self.ws.send(orjson.dumps(sub_msg))

        msg = await self.ws.recv()
        data = orjson.loads(msg)
        log.info(f"Subscription response: {data}")

    async def run(self):
        """Main loop - receive and dispatch messages"""
        self.running = True
        log.info("Starting message loop")

        try:
            while self.running:
                try:
                    msg = await asyncio.wait_for(self.ws.recv(), timeout=30)
                    data = orjson.loads(msg)

                    for item in data:
                        msg_type = item.get("T")

                        if msg_type == "t" and self.on_trade:
                            # Trade message
                            await self.on_trade(
                                symbol=item["S"],
                                price=item["p"],
                                size=item["s"],
                                timestamp=item["t"],
                            )

                        elif msg_type == "b" and self.on_bar:
                            # Bar message
                            await self.on_bar(
                                symbol=item["S"],
                                bar={
                                    "open": item["o"],
                                    "high": item["h"],
                                    "low": item["l"],
                                    "close": item["c"],
                                    "volume": item["v"],
                                    "timestamp": item["t"],
                                },
                            )

                        elif msg_type == "q" and self.on_quote:
                            # Quote message
                            await self.on_quote(
                                symbol=item["S"],
                                bid=item["bp"],
                                ask=item["ap"],
                                bid_size=item["bs"],
                                ask_size=item["as"],
                                timestamp=item["t"],
                            )

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await self.ws.ping()

        except websockets.ConnectionClosed as e:
            log.warning(f"WebSocket closed: {e}")
            self.running = False

    async def close(self):
        """Close the WebSocket connection"""
        self.running = False
        if self.ws:
            await self.ws.close()
            log.info("WebSocket closed")
