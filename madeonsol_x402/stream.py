"""Real-time WebSocket streaming client.

Wraps the connect -> token -> subscribe -> event loop with auto-reconnect,
24h-token auto-refresh, heartbeat liveness (via websockets ping/pong), and
typed callbacks, so consumers never hand-roll connection management. Obtain one
via ``client.stream()``.

Requires the optional ``websockets`` dependency:
    pip install "madeonsol-x402[stream]"
"""
from __future__ import annotations

import asyncio
import inspect
import json
import random
from typing import Any, Awaitable, Callable

# Channels you can subscribe to.
CHANNELS = (
    "kol:trades",
    "kol:coordination",
    "kol:first_touches",
    "deployer:alerts",
    "wallet_tracker:events",
    "copytrade:signals",
    "price_alert:events",
    "sniper:deploys",
    "token:graduations",
)

# Event names delivered on those channels.
EVENT_NAMES = (
    "kol:trade",
    "kol:coordination",
    "kol:first_touch",
    "deployer:alert",
    "deployer:bond",
    "wallet_tracker:event",
    "copytrade:signal",
    "price_alert:dip",
    "price_alert:recovery",
    "sniper:deploy",
    "token:graduation",
)

Handler = Callable[..., Any | Awaitable[Any]]
TokenProvider = Callable[[], Awaitable[dict[str, Any]]]


def _arity(fn: Handler) -> int:
    try:
        return len(inspect.signature(fn).parameters)
    except (TypeError, ValueError):
        return 1


class MadeOnSolStream:
    """Managed WebSocket stream.

    Example::

        stream = client.stream()

        @stream.on("kol:trade")
        async def on_trade(data, evt):
            print(data["token_symbol"], data["action"])

        stream.subscribe(["kol:trades", "deployer:alerts"])
        await stream.run()   # blocks; manages connection + reconnects
    """

    def __init__(
        self,
        get_token: TokenProvider,
        *,
        auto_reconnect: bool = True,
        max_backoff: float = 30.0,
    ) -> None:
        self._get_token = get_token
        self.auto_reconnect = auto_reconnect
        self.max_backoff = max_backoff
        self._handlers: dict[str, list[Handler]] = {}
        self._channels: set[str] = set()
        self._filters: dict[str, Any] = {}
        self._ws: Any = None
        self._running = False
        self._attempt = 0

    def on(self, event: str, fn: Handler | None = None):
        """Register a handler. Use an event name, ``"*"`` for all events, or a
        lifecycle event (``open`` / ``close`` / ``reconnect`` / ``subscribed`` /
        ``heartbeat`` / ``error``). Usable as a decorator."""
        def register(f: Handler) -> Handler:
            self._handlers.setdefault(event, []).append(f)
            return f
        return register(fn) if fn is not None else register

    def subscribe(self, channels: list[str], filters: dict[str, Any] | None = None) -> "MadeOnSolStream":
        """Subscribe to channels (sent on connect, or immediately if connected)."""
        self._channels.update(channels)
        if filters:
            self._filters.update(filters)
        if self._ws is not None:
            asyncio.ensure_future(self._send_subscribe())
        return self

    def unsubscribe(self, channels: list[str]) -> "MadeOnSolStream":
        for c in channels:
            self._channels.discard(c)
        if self._ws is not None:
            asyncio.ensure_future(self._ws.send(json.dumps({"type": "unsubscribe", "channels": channels})))
        return self

    async def _send_subscribe(self) -> None:
        if self._ws is None or not self._channels:
            return
        msg: dict[str, Any] = {"type": "subscribe", "channels": sorted(self._channels)}
        if self._filters:
            msg["filters"] = self._filters
        await self._ws.send(json.dumps(msg))

    async def _emit(self, event: str, data: Any, evt: dict | None = None) -> None:
        for fn in self._handlers.get(event, []):
            try:
                result = fn(data, evt) if _arity(fn) >= 2 else fn(data)
                if inspect.isawaitable(result):
                    await result
            except Exception:  # user handler error must not kill the stream
                pass

    async def run(self) -> None:
        """Connect and run the receive loop, reconnecting on drop. Blocks until
        :meth:`close` is called (or ``auto_reconnect`` is False and the socket
        drops)."""
        try:
            import websockets  # noqa: F401  (optional dependency)
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "WebSocket streaming requires the 'websockets' package. "
                "Install with: pip install \"madeonsol-x402[stream]\""
            ) from exc
        import websockets

        self._running = True
        while self._running:
            try:
                tok = await self._get_token()
                url = f"{tok['ws_url']}?token={tok['token']}"
                async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                    self._ws = ws
                    self._attempt = 0
                    if self._channels:
                        await self._send_subscribe()
                    await self._emit("open", None)
                    async for raw in ws:
                        await self._handle(raw)
            except Exception as exc:  # noqa: BLE001 — surface, then reconnect
                await self._emit("error", exc)
            finally:
                self._ws = None
                await self._emit("close", None)
            if not self._running or not self.auto_reconnect:
                break
            delay = min(2 ** self._attempt, self.max_backoff)
            self._attempt += 1
            await self._emit("reconnect", {"attempt": self._attempt, "delay": delay})
            await asyncio.sleep(delay / 2 + random.random() * delay / 2)

    async def _handle(self, raw: Any) -> None:
        try:
            msg = json.loads(raw)
        except Exception:
            await self._emit("error", ValueError("failed to parse stream message"))
            return
        mtype = msg.get("type")
        if mtype == "heartbeat":
            await self._emit("heartbeat", msg.get("ts"))
            return
        if mtype == "connected":
            return
        if mtype == "subscribed":
            await self._emit("subscribed", msg.get("channels"))
            return
        if msg.get("channel") and msg.get("event"):
            await self._emit(msg["event"], msg.get("data"), msg)
            await self._emit("*", msg.get("data"), msg)

    async def close(self) -> None:
        """Stop reconnecting and close the socket."""
        self._running = False
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
            self._ws = None
