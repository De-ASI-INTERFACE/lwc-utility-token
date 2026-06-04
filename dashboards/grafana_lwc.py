"""Grafana Dashboard Config Generator — LWC Monitoring

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Generate and push Grafana dashboard JSON for LWC ecosystem monitoring.
         Integrates with grafana-monitoring repo.

Dashboards:
  - LWC Market Data     — price, volume, liquidity depth, spread, large transfer alerts
  - LWC Staking         — total staked, APY, staker count, upcoming unlocks
  - LWC Governance      — active proposals, participation rate, top voters
  - LWC MM P&L          — daily P&L, inventory skew, spread capture, adverse selection
  - LWC Fee Engine      — burn rate, treasury flow, LP reward accrual

Design:
  - Iterative dashboard + panel assembly — no recursion
  - Memory-safe: build each dashboard dict in a single pass
"""
import json
import os
from typing import Dict, List
from loguru import logger


def _panel(title: str, panel_id: int, expr: str, panel_type: str = "timeseries") -> dict:
    """Build a single Grafana panel dict."""
    return {
        "id":      panel_id,
        "title":   title,
        "type":    panel_type,
        "targets": [{"expr": expr, "legendFormat": title}],
        "gridPos": {"h": 8, "w": 12, "x": (panel_id % 2) * 12, "y": (panel_id // 2) * 8},
    }


DASHBOARD_SPECS: Dict[str, List[tuple]] = {
    "LWC_Market_Data": [
        ("LWC/USD Price",           "lwc_price_usd"),
        ("24h Volume (LWC)",         "lwc_volume_24h"),
        ("Pool Liquidity Depth",     "lwc_liquidity_depth"),
        ("Bid-Ask Spread (bps)",     "lwc_spread_bps"),
        ("Large Transfers >100k LWC","lwc_large_transfer_count"),
    ],
    "LWC_Staking": [
        ("Total LWC Staked",         "lwc_total_staked"),
        ("Staking APY (%)",           "lwc_staking_apy"),
        ("Active Stakers",           "lwc_staker_count"),
        ("Avg Stake Size (LWC)",     "lwc_avg_stake"),
        ("Unlocks Next 7 Days (LWC)","lwc_upcoming_unlocks_7d"),
    ],
    "LWC_Governance": [
        ("Active Proposals",         "lwc_active_proposals"),
        ("Voting Participation (%)", "lwc_vote_participation_pct"),
        ("Proposals Passed (30d)",   "lwc_proposals_passed_30d"),
    ],
    "LWC_MM_PnL": [
        ("MM Daily P&L (USD)",        "lwc_mm_daily_pnl"),
        ("Inventory Skew",            "lwc_mm_inventory_skew"),
        ("Spread Capture (LWC)",      "lwc_mm_spread_capture"),
        ("Adverse Selection Loss",    "lwc_mm_adverse_selection"),
    ],
    "LWC_Fee_Engine": [
        ("LWC Burned (cumulative)",   "lwc_burned_total"),
        ("Treasury Inflow (LWC)",     "lwc_treasury_inflow"),
        ("LP Reward Accrual (LWC)",   "lwc_lp_reward_accrual"),
        ("Fee Revenue (USD)",         "lwc_fee_revenue_usd"),
    ],
}


def build_dashboard(name: str, panels_spec: List[tuple]) -> dict:
    """Iteratively assemble a Grafana dashboard dict."""
    panels = []
    for idx, (title, expr) in enumerate(panels_spec):
        panels.append(_panel(title, idx, expr))
    return {
        "title":       name.replace("_", " "),
        "uid":         name.lower(),
        "schemaVersion": 38,
        "panels":      panels,
        "refresh":      "10s",
        "tags":         ["lwc", "solana", "deasi"],
        "__creator__":  "Richard Patterson (@De-ASI-INTERFACE)",
    }


def export_all_dashboards(output_dir: str = "dashboards/json") -> None:
    """Build and write all LWC Grafana dashboards to JSON files."""
    os.makedirs(output_dir, exist_ok=True)
    for name, spec in DASHBOARD_SPECS.items():
        dashboard = build_dashboard(name, spec)
        path = os.path.join(output_dir, f"{name.lower()}.json")
        with open(path, "w") as fh:
            json.dump(dashboard, fh, indent=2)
        logger.info(f"[Grafana] Exported: {path} ({len(spec)} panels)")
    logger.success(f"[Grafana] All {len(DASHBOARD_SPECS)} dashboards exported to {output_dir}")


if __name__ == "__main__":
    export_all_dashboards()
