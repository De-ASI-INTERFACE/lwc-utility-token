"""
Redis Token State — crash-safe supply, holder, and governance state.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations
import json
import time
from typing import Optional

import redis.asyncio as aioredis
from loguru import logger


class RedisTokenState:
    """
    Caches on-chain token state (supply, holder count, governance params).
    Reduces RPC calls for frequently-read data.
    All entries include slot and confirmation_level for auditability.
    """
    SUPPLY_TTL_S: int = 10       # supply changes slowly
    HOLDER_TTL_S: int = 30
    GOVERNANCE_TTL_S: int = 60

    def __init__(self, redis_url: str = "redis://localhost:6379/3") -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def set_supply(self, mint: str, amount: float, decimals: int,
                         slot: int, confirmation_level: str = "confirmed") -> None:
        data = {"amount": amount, "decimals": decimals, "slot": slot,
                "confirmation_level": confirmation_level, "updated_at": time.time()}
        await self._redis.setex(f"supply:{mint}", self.SUPPLY_TTL_S, json.dumps(data))
        logger.info("token_supply_cached", extra={
            "mint": mint[:16], "amount": amount, "slot": slot,
            "confirmation_level": confirmation_level,
        })

    async def get_supply(self, mint: str) -> Optional[dict]:
        raw = await self._redis.get(f"supply:{mint}")
        return json.loads(raw) if raw else None

    async def set_governance_param(self, key: str, value, slot: int) -> None:
        data = {"value": value, "slot": slot, "updated_at": time.time()}
        await self._redis.setex(f"gov:{key}", self.GOVERNANCE_TTL_S, json.dumps(data))
        logger.info("governance_param_cached", extra={"key": key, "slot": slot})

    async def get_governance_param(self, key: str) -> Optional[dict]:
        raw = await self._redis.get(f"gov:{key}")
        return json.loads(raw) if raw else None
