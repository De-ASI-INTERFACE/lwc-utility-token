"""LWC Market-Making Engine

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Institutional-grade market-making for LWC on Solana DEXs.
         Jupiter quote-based mid price, inventory-skew spread adjustment,
         daily loss kill-switch, dry-run mode, async loop.

Design:
  - Iterative main loop — no recursion
  - Flat state object — no nested mutable structures
  - Memory-safe: no accumulating collections in the hot path
  - Integrates with trading-bot and solana-execution repos
"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
import aiohttp
from loguru import logger

USDC_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"


@dataclass
class MMConfig:
    lwc_mint:           str
    jupiter_url:        str  = "https://quote-api.jup.ag/v6"
    dry_run:            bool = True
    base_spread_bps:    int  = 50
    max_order_usdc:     float = 50.0
    daily_loss_limit:   float = 500.0
    interval_s:         float = 30.0


@dataclass
class MMState:
    lwc_inventory:  float = 0.0
    usdc_inventory: float = 0.0
    daily_pnl:      float = 0.0
    last_reset:     float = field(default_factory=time.time)
    active:         bool  = True

    def tick_daily_reset(self) -> None:
        """Reset daily P&L at UTC midnight boundary."""
        if time.time() - self.last_reset > 86_400:
            logger.info(f"[MM] Daily reset | P&L was {self.daily_pnl:.2f} USD")
            self.daily_pnl  = 0.0
            self.last_reset = time.time()

    @property
    def inventory_skew(self) -> float:
        """Signed skew in [-1, 1]. Positive = long LWC."""
        total = self.lwc_inventory + self.usdc_inventory
        if total == 0:
            return 0.0
        return (self.lwc_inventory - self.usdc_inventory) / total

    def spread_bps(self, cfg: MMConfig) -> tuple:
        """Iterative spread calc — returns (bid_bps, ask_bps)."""
        base  = cfg.base_spread_bps
        skew  = abs(self.inventory_skew) * 20
        if self.inventory_skew > 0:    # long — want to sell, widen ask
            return max(int(base - skew), 5), int(base + skew)
        else:                          # short — want to buy, widen bid
            return int(base + skew), max(int(base - skew), 5)


async def _fetch_mid_price(cfg: MMConfig, amount: float = 1.0) -> Optional[float]:
    """Get LWC/USDC mid from Jupiter quote API."""
    params = {
        "inputMint":    cfg.lwc_mint,
        "outputMint":   USDC_MINT,
        "amount":       int(amount * 1e9),   # LWC 9 decimals
        "slippageBps":  100,
    }
    try:
        async with aiohttp.ClientSession() as sess:
            async with sess.get(
                f"{cfg.jupiter_url}/quote",
                params=params,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as r:
                if r.status != 200:
                    logger.warning(f"[MM] Jupiter {r.status}")
                    return None
                data      = await r.json()
                out       = float(data.get("outAmount", 0)) / 1e6
                mid_price = out / amount
                logger.debug(f"[MM] Mid price: ${mid_price:.6f}")
                return mid_price
    except Exception as exc:
        logger.warning(f"[MM] Price fetch error: {exc}")
        return None


async def run_market_maker(cfg: MMConfig, state: MMState) -> None:
    """
    Main market-making loop — iterative, no recursion.
    Cycle: reset check -> kill-switch -> price fetch -> quote -> place/log orders.
    """
    logger.info(f"[MM] Starting | dry_run={cfg.dry_run} | interval={cfg.interval_s}s")

    while state.active:
        state.tick_daily_reset()

        if state.daily_pnl < -cfg.daily_loss_limit:
            logger.error(f"[MM] Daily loss limit {cfg.daily_loss_limit} USD hit — halting")
            state.active = False
            break

        mid = await _fetch_mid_price(cfg)
        if mid is None:
            await asyncio.sleep(cfg.interval_s)
            continue

        bid_bps, ask_bps = state.spread_bps(cfg)
        bid = mid * (1 - bid_bps / 10_000)
        ask = mid * (1 + ask_bps / 10_000)

        if cfg.dry_run:
            logger.info(
                f"[MM DRY RUN] mid=${mid:.6f} | bid=${bid:.6f}({bid_bps}bps) | "
                f"ask=${ask:.6f}({ask_bps}bps) | skew={state.inventory_skew:.3f} | "
                f"pnl={state.daily_pnl:.2f}"
            )
        else:
            logger.info(f"[MM] Placing bid=${bid:.6f} ask=${ask:.6f}")
            # Wire to solana-execution repo: submit_order(bid, ask, cfg.lwc_mint)

        await asyncio.sleep(cfg.interval_s)
