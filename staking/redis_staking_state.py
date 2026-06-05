"""
Redis Staking State — crash-safe staking positions and reward accounting.
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
class StakePosition:
    pubkey: str
    amount: float
    staked_at_slot: int
    unlock_slot: int
    rewards_earned: float = 0.0
    confirmation_level: str = "confirmed"
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.updated_at:
            self.updated_at = time.time()


class RedisStakingState:
    def __init__(self, redis_url: str = "redis://localhost:6379/4") -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)
        self._positions: dict[str, StakePosition] = {}

    async def restore(self) -> None:
        raw = await self._redis.hgetall("stake_positions")
        for pk, data in raw.items():
            self._positions[pk] = StakePosition(**json.loads(data))
        logger.info("staking_state_restored", extra={"positions": len(self._positions)})

    async def open_stake(self, pubkey: str, amount: float,
                         staked_at_slot: int, unlock_slot: int) -> StakePosition:
        pos = StakePosition(pubkey=pubkey, amount=amount,
                            staked_at_slot=staked_at_slot, unlock_slot=unlock_slot)
        self._positions[pubkey] = pos
        await self._redis.hset("stake_positions", pubkey, json.dumps(asdict(pos)))
        logger.info("stake_opened", extra={
            "pubkey": pubkey[:16], "amount": amount,
            "slot": staked_at_slot, "unlock_slot": unlock_slot,
            "confirmation_level": "confirmed",
        })
        return pos

    async def accrue_reward(self, pubkey: str, reward: float, slot: int) -> None:
        pos = self._positions.get(pubkey)
        if not pos:
            return
        pos.rewards_earned += reward
        pos.updated_at = time.time()
        await self._redis.hset("stake_positions", pubkey, json.dumps(asdict(pos)))
        logger.info("reward_accrued", extra={
            "pubkey": pubkey[:16], "reward": reward,
            "total_rewards": pos.rewards_earned, "slot": slot,
            "confirmation_level": "finalized",
        })

    async def close_stake(self, pubkey: str, slot: int) -> Optional[StakePosition]:
        pos = self._positions.pop(pubkey, None)
        if pos:
            await self._redis.hdel("stake_positions", pubkey)
            logger.info("stake_closed", extra={
                "pubkey": pubkey[:16], "total_rewards": pos.rewards_earned,
                "slot": slot, "confirmation_level": "finalized",
            })
        return pos
