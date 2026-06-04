"""DeASI AI API Subscription Engine — LWC-gated access

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Gate DeASI AI API tiers by LWC stake or payment.
         Iterative tier lookup — no recursion.

Tiers:
  basic:      100 LWC/month  — 1k req/day,   basic signals
  pro:        500 LWC/month  — 10k req/day,  advanced signals + priority support
  enterprise: 2000 LWC/month — 100k req/day, full access + SLA + custom integrations
"""
import time
from dataclasses import dataclass, field
from typing import Dict, Optional
from loguru import logger

TIERS: Dict[str, dict] = {
    "basic":      {"lwc_per_month": 100,   "req_per_day": 1_000,    "features": ["Basic AI signals", "Market data feed"]},
    "pro":        {"lwc_per_month": 500,   "req_per_day": 10_000,   "features": ["Advanced AI signals", "Priority support", "Custom indicators", "WebSocket stream"]},
    "enterprise": {"lwc_per_month": 2_000, "req_per_day": 100_000,  "features": ["Full API access", "Dedicated support", "Custom integrations", "99.9% SLA", "On-chain analytics"]},
}


@dataclass
class Subscription:
    wallet:     str
    tier:       str
    lwc_paid:   float
    activated:  float = field(default_factory=time.time)
    duration_s: int   = 2_592_000  # 30 days

    @property
    def expires_at(self) -> float:
        return self.activated + self.duration_s

    @property
    def is_active(self) -> bool:
        return time.time() < self.expires_at

    @property
    def req_per_day(self) -> int:
        return TIERS.get(self.tier, {}).get("req_per_day", 0)

    @property
    def features(self) -> list:
        return TIERS.get(self.tier, {}).get("features", [])


_SUBSCRIPTIONS: Dict[str, Subscription] = {}


def available_tiers() -> Dict[str, dict]:
    """Return copy of tier config. Iterative build — no recursion."""
    return {k: dict(v) for k, v in TIERS.items()}


def get_tier_for_amount(lwc_amount: float) -> Optional[str]:
    """Iteratively find the highest tier the given LWC amount qualifies for."""
    best: Optional[str] = None
    for tier_name, tier_cfg in TIERS.items():
        if lwc_amount >= tier_cfg["lwc_per_month"]:
            if best is None or tier_cfg["lwc_per_month"] > TIERS[best]["lwc_per_month"]:
                best = tier_name
    return best


def activate_subscription(wallet: str, lwc_amount: float) -> Subscription:
    """Activate the best tier the wallet qualifies for based on LWC amount."""
    tier = get_tier_for_amount(lwc_amount)
    if tier is None:
        raise ValueError(
            f"[API] {lwc_amount:.0f} LWC is below minimum tier (100 LWC). "
            f"Available: {list(TIERS.keys())}"
        )
    sub = Subscription(wallet=wallet, tier=tier, lwc_paid=lwc_amount)
    _SUBSCRIPTIONS[wallet] = sub
    logger.info(
        f"[API] {wallet[:8]}... activated '{tier}' tier | "
        f"paid={lwc_amount:.0f} LWC | req/day={sub.req_per_day:,} | expires={sub.expires_at:.0f}"
    )
    return sub


def check_access(wallet: str) -> bool:
    """Return True if wallet has an active subscription."""
    sub = _SUBSCRIPTIONS.get(wallet)
    if sub is None or not sub.is_active:
        logger.warning(f"[API] {wallet[:8]}... has no active subscription")
        return False
    return True


def get_subscription(wallet: str) -> Optional[Subscription]:
    """Return active subscription or None."""
    sub = _SUBSCRIPTIONS.get(wallet)
    return sub if sub and sub.is_active else None
