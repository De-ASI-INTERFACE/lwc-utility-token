"""
Redis Market-Making State — order book and inventory crash-safe persistence.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations
import json
import time
from dataclasses import asdict, dataclass
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger


@dataclass
class MMOrder:
    order_id: str
    symbol: str
    side: str        # bid | ask
    price: float
    qty: float
    slot: int
    status: str = "open"   # open | filled | cancelled
    confirmation_level: str = "processed"
    created_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()


class RedisMMState:
    """
    Persists active MM orders and inventory position.
    On crash recovery, call restore() to rebuild in-memory state.
    """
    def __init__(self, redis_url: str = "redis://localhost:6379/5") -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._orders: dict[str, MMOrder] = {}
        self._inventory: dict[str, float] = {}

    async def restore(self) -> None:
        raw_orders = await self._redis.hgetall("mm_orders")
        for oid, data in raw_orders.items():
            self._orders[oid] = MMOrder(**json.loads(data))
        raw_inv = await self._redis.hgetall("mm_inventory")
        for symbol, qty in raw_inv.items():
            self._inventory[symbol] = float(qty)
        logger.info("mm_state_restored", extra={
            "orders": len(self._orders), "inventory_symbols": len(self._inventory),
        })

    async def place_order(self, order: MMOrder) -> None:
        self._orders[order.order_id] = order
        await self._redis.hset("mm_orders", order.order_id, json.dumps(asdict(order)))
        logger.info("mm_order_placed", extra={
            "order_id": order.order_id, "symbol": order.symbol,
            "side": order.side, "price": order.price, "qty": order.qty,
            "slot": order.slot, "confirmation_level": order.confirmation_level,
        })

    async def fill_order(self, order_id: str, slot: int) -> Optional[MMOrder]:
        order = self._orders.pop(order_id, None)
        if order:
            order.status = "filled"
            await self._redis.hdel("mm_orders", order_id)
            inv_delta = order.qty if order.side == "bid" else -order.qty
            await self._redis.hincrbyfloat("mm_inventory", order.symbol, inv_delta)
            self._inventory[order.symbol] = self._inventory.get(order.symbol, 0) + inv_delta
            logger.info("mm_order_filled", extra={
                "order_id": order_id, "symbol": order.symbol,
                "slot": slot, "confirmation_level": "confirmed",
                "inventory": self._inventory.get(order.symbol, 0),
            })
        return order

    def get_inventory(self, symbol: str) -> float:
        return self._inventory.get(symbol, 0.0)
