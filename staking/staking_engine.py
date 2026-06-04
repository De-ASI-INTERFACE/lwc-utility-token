"""LWC Staking Engine

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Memory-efficient, iterative staking engine for LWC.
         Manages stake positions, time-weighted voting power, and reward accrual.

Design:
  - Flat dict-based registry — O(1) lookup, no tree traversal, no recursion
  - Generators used for all bulk reads to avoid materializing large lists
  - Time-weighted power multipliers: 30d=1.25x, 90d=1.5x, 180d+=2x
"""
import time
from dataclasses import dataclass, field
from typing import Dict, Generator, Optional
from loguru import logger


@dataclass
class StakePosition:
    wallet:               str
    amount:               float
    staked_at:            float = field(default_factory=time.time)
    lock_seconds:         int   = 0
    accumulated_rewards:  float = 0.0

    @property
    def unlock_ts(self) -> float:
        return self.staked_at + self.lock_seconds

    @property
    def is_unlocked(self) -> bool:
        return time.time() >= self.unlock_ts

    @property
    def lock_days(self) -> float:
        return self.lock_seconds / 86_400

    @property
    def power_multiplier(self) -> float:
        """Time-weighted multiplier based on lock duration."""
        d = self.lock_days
        if d >= 180:
            return 2.0
        if d >= 90:
            return 1.5
        if d >= 30:
            return 1.25
        return 1.0

    @property
    def voting_power(self) -> float:
        return self.amount * self.power_multiplier


# Flat in-memory registry — replace with on-chain PDA reads in production
_REGISTRY: Dict[str, StakePosition] = {}


def stake(wallet: str, amount: float, lock_seconds: int = 0) -> StakePosition:
    """Open or add to a stake position."""
    if amount <= 0:
        raise ValueError(f"[Staking] Amount must be positive, got {amount}")
    if wallet in _REGISTRY:
        # Top-up existing position without resetting lock
        _REGISTRY[wallet].amount += amount
        pos = _REGISTRY[wallet]
    else:
        pos = StakePosition(wallet=wallet, amount=amount, lock_seconds=lock_seconds)
        _REGISTRY[wallet] = pos
    logger.info(
        f"[Staking] {wallet[:8]}... staked {amount:.2f} LWC "
        f"(total={pos.amount:.2f}, lock={pos.lock_days:.0f}d, power={pos.voting_power:.2f})"
    )
    return pos


def unstake(wallet: str) -> float:
    """Close a stake position and return amount if lock expired."""
    pos = _REGISTRY.get(wallet)
    if pos is None:
        raise KeyError(f"[Staking] No position for {wallet[:8]}...")
    if not pos.is_unlocked:
        remaining = int(pos.unlock_ts - time.time())
        raise PermissionError(f"[Staking] Still locked for {remaining}s")
    amount = pos.amount
    del _REGISTRY[wallet]
    logger.info(f"[Staking] {wallet[:8]}... unstaked {amount:.2f} LWC")
    return amount


def get_power(wallet: str) -> float:
    """Return voting power for a wallet (0.0 if not staked)."""
    pos = _REGISTRY.get(wallet)
    return pos.voting_power if pos else 0.0


def total_staked() -> float:
    """Sum of all staked amounts — iterative, no recursion."""
    total = 0.0
    for pos in _REGISTRY.values():
        total += pos.amount
    return total


def total_voting_power() -> float:
    """Sum of all time-weighted voting power."""
    power = 0.0
    for pos in _REGISTRY.values():
        power += pos.voting_power
    return power


def iter_positions() -> Generator[StakePosition, None, None]:
    """Memory-safe generator over all active stake positions."""
    for pos in _REGISTRY.values():
        yield pos


def distribute_rewards(total_reward_pool: float) -> Dict[str, float]:
    """
    Distribute reward pool proportionally by voting power.
    Iterative — no recursion. Returns dict of wallet -> reward.
    """
    total_power = total_voting_power()
    if total_power == 0:
        logger.warning("[Staking] No staked LWC — rewards not distributed")
        return {}

    rewards: Dict[str, float] = {}
    for pos in iter_positions():
        share = pos.voting_power / total_power
        reward = total_reward_pool * share
        pos.accumulated_rewards += reward
        rewards[pos.wallet] = reward
        logger.debug(f"[Staking] Reward {pos.wallet[:8]}...: {reward:.4f} LWC ({share*100:.2f}%)")

    logger.info(f"[Staking] Distributed {total_reward_pool:.4f} LWC across {len(rewards)} stakers")
    return rewards
