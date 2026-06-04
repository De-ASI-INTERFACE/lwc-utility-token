"""LWC AMM Fee Configuration.
All fee logic is iterative and stateless.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

FEE_TIERS: dict[str, float] = {
    "standard": 0.003,   # 0.30%
    "stable": 0.0005,    # 0.05%
    "exotic": 0.01,      # 1.00%
}

UBI_TREASURY_SPLIT: float = 0.30   # 30% of fees to treasury
LWC_BUYBACK_SPLIT: float = 0.30    # 30% of fees to LWC buyback-burn
LP_REWARDS_SPLIT: float = 0.40     # 40% of fees to LPs


def calculate_fee(amount: float, tier: str = "standard") -> dict:
    """Calculate fee breakdown for a swap."""
    rate = FEE_TIERS.get(tier, FEE_TIERS["standard"])
    total_fee = amount * rate
    return {
        "gross_amount": amount,
        "fee_rate": rate,
        "total_fee": total_fee,
        "to_treasury": total_fee * UBI_TREASURY_SPLIT,
        "to_buyback": total_fee * LWC_BUYBACK_SPLIT,
        "to_lp": total_fee * LP_REWARDS_SPLIT,
        "net_amount": amount - total_fee,
    }


def batch_fee_summary(trades: list[dict]) -> dict:
    """Aggregate fee totals across a list of trades — fully iterative."""
    totals: dict[str, float] = {
        "total_volume": 0.0,
        "total_fee": 0.0,
        "to_treasury": 0.0,
        "to_buyback": 0.0,
        "to_lp": 0.0,
    }
    for trade in trades:
        result = calculate_fee(trade.get("amount", 0), trade.get("tier", "standard"))
        totals["total_volume"] += result["gross_amount"]
        totals["total_fee"] += result["total_fee"]
        totals["to_treasury"] += result["to_treasury"]
        totals["to_buyback"] += result["to_buyback"]
        totals["to_lp"] += result["to_lp"]
    return totals
