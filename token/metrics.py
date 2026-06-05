"""
Prometheus Metrics — LWC token, staking, and market-making observability.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations
try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

if PROMETHEUS_AVAILABLE:
    # Token
    transfers_total = Counter("lwc_token_transfers_total", "Total LWC token transfers", ["direction"])
    transfer_volume = Counter("lwc_token_transfer_volume", "Total LWC transfer volume", ["direction"])
    supply_gauge = Gauge("lwc_token_supply", "Current LWC circulating supply")

    # Staking
    stakes_opened = Counter("lwc_staking_opened_total", "Staking positions opened")
    stakes_closed = Counter("lwc_staking_closed_total", "Staking positions closed")
    rewards_distributed = Counter("lwc_staking_rewards_total", "Total rewards distributed")
    active_stakes = Gauge("lwc_staking_active_positions", "Currently active staking positions")

    # Market making
    mm_orders_placed = Counter("lwc_mm_orders_placed_total", "MM orders placed", ["side"])
    mm_orders_filled = Counter("lwc_mm_orders_filled_total", "MM orders filled", ["side"])
    mm_inventory = Gauge("lwc_mm_inventory", "Current MM inventory", ["symbol"])
    mm_spread_bps = Gauge("lwc_mm_spread_bps", "Current quoted spread in basis points", ["symbol"])

    # RPC
    rpc_latency = Histogram(
        "lwc_rpc_latency_ms", "Solana RPC latency (ms)",
        ["endpoint"], buckets=[1, 5, 10, 25, 50, 100, 250, 500],
    )

    def start_metrics_server(port: int = 8004) -> None:
        start_http_server(port)
else:
    def start_metrics_server(port: int = 8004) -> None:
        pass
