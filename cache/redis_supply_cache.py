#!/usr/bin/env python3
"""
Redis Supply Cache — Caches LWC token supply for AMM, staking, and market-making modules.
Redis keys: lwc:supply:amm, lwc:supply:staking, lwc:supply:marketmaking
Repo: lwc-utility-token | Author: Richard Patterson (@De-ASI-INTERFACE)
"""

import asyncio
import json
import logging
import os
import time
import redis.asyncio as aioredis
from solana.rpc_client import SolanaRPCClient

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
)
logger = logging.getLogger("lwc.supply_cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
LWC_MINT_ADDRESS = os.getenv("LWC_MINT_ADDRESS", "")
SUPPLY_CACHE_TTL = int(os.getenv("SUPPLY_CACHE_TTL", 30))
REFRESH_INTERVAL = int(os.getenv("SUPPLY_REFRESH_INTERVAL", 15))

MODULE_KEYS = {
    "amm": "lwc:supply:amm",
    "staking": "lwc:supply:staking",
    "marketmaking": "lwc:supply:marketmaking"
}


async def refresh_supply_cache(redis: aioredis.Redis, rpc: SolanaRPCClient):
    """Fetch LWC token supply and write to all module Redis keys."""
    supply_data = await rpc.get_token_supply(LWC_MINT_ADDRESS)
    slot = await rpc.get_slot()

    payload = {
        "amount": supply_data.get("amount", "0"),
        "decimals": supply_data.get("decimals", 9),
        "uiAmount": supply_data.get("uiAmount", 0.0),
        "slot": slot,
        "refreshed_at": time.time()
    }

    for module, key in MODULE_KEYS.items():
        await redis.setex(key, SUPPLY_CACHE_TTL, json.dumps(payload))
        logger.info(f"Supply cached: module={module} key={key} slot={slot} uiAmount={payload['uiAmount']}")


async def run_supply_cache_loop():
    redis = aioredis.from_url(REDIS_URL)
    rpc = SolanaRPCClient()
    logger.info("LWC Redis supply cache loop started")
    try:
        while True:
            try:
                await refresh_supply_cache(redis, rpc)
            except Exception as e:
                logger.error(f"Supply cache error: {e}")
            await asyncio.sleep(REFRESH_INTERVAL)
    finally:
        await rpc.close()


if __name__ == "__main__":
    asyncio.run(run_supply_cache_loop())
