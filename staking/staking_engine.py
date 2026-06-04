"""LWC Staking Engine — memory-optimized, fully iterative.
Uses dict + deque for O(1) lookups. Zero recursion.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque
from loguru import logger


@dataclass
class StakePosition:
    wallet: str
    amount_lwc: float
    locked_until: float  # unix timestamp
    multiplier: float = 1.0
    entered_at: float = field(default_factory=time.time)


class StakingEngine:
    """Manages LWC staking positions with O(1) wallet lookups."""

    def __init__(self) -> None:
        self._positions: dict[str, StakePosition] = {}
        self._event_log: Deque[dict] = deque(maxlen=10_000)
        self._total_staked: float = 0.0

    def stake(self, wallet: str, amount: float, lock_days: int = 0) -> bool:
        """Add or increase a staking position."""
        if amount <= 0:
            logger.warning(f"Invalid stake amount: {amount}")
            return False

        lock_seconds = lock_days * 86_400
        multiplier = 1.0 + (lock_days / 365) * 0.5  # 50% bonus APY boost per year locked

        if wallet in self._positions:
            pos = self._positions[wallet]
            pos.amount_lwc += amount
            pos.locked_until = max(pos.locked_until, time.time() + lock_seconds)
            pos.multiplier = multiplier
        else:
            self._positions[wallet] = StakePosition(
                wallet=wallet,
                amount_lwc=amount,
                locked_until=time.time() + lock_seconds,
                multiplier=multiplier,
            )

        self._total_staked += amount
        self._event_log.append({"event": "stake", "wallet": wallet, "amount": amount, "ts": time.time()})
        logger.info(f"Staked {amount} LWC for {wallet} (multiplier={multiplier:.2f}x)")
        return True

    def unstake(self, wallet: str) -> float:
        """Remove a staking position if unlock time has passed."""
        pos = self._positions.get(wallet)
        if pos is None:
            logger.warning(f"No stake found for {wallet}")
            return 0.0
        if time.time() < pos.locked_until:
            remaining = pos.locked_until - time.time()
            logger.warning(f"{wallet} locked for {remaining:.0f}s more")
            return 0.0

        amount = pos.amount_lwc
        del self._positions[wallet]
        self._total_staked -= amount
        self._event_log.append({"event": "unstake", "wallet": wallet, "amount": amount, "ts": time.time()})
        logger.info(f"Unstaked {amount} LWC for {wallet}")
        return amount

    def get_position(self, wallet: str) -> StakePosition | None:
        return self._positions.get(wallet)

    def total_staked(self) -> float:
        return self._total_staked

    def top_stakers(self, n: int = 10) -> list[StakePosition]:
        """Return top n stakers by amount — iterative sort."""
        sorted_positions: list[StakePosition] = sorted(
            self._positions.values(), key=lambda p: p.amount_lwc, reverse=True
        )
        return sorted_positions[:n]
