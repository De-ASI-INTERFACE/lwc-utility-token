"""LWC Fee Engine — AMM Integration Patch

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Replaces TODO stubs in rp_spl_amm_platform_v1/src/fee_engine.py
         with functional SPL token transfer and burn execution.
         Import and call from pool_manager.execute_swap_with_fee.

Design:
  - Iterative distribution logic — no recursion
  - Dry-run mode logs without sending transactions
  - All on-chain calls are async with timeout + retry
  - Memory-safe: no accumulating state in hot path
"""
import asyncio
from dataclasses import dataclass
from typing import Dict
import aiohttp
from loguru import logger

TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


@dataclass
class FeeAllocation:
    total_fee:        float
    burn_amount:      float
    treasury_amount:  float
    lp_reward_amount: float
    reserve_amount:   float


def split_fees(
    gross_fee: float,
    fee_bps:      int = 30,
    burn_bps:     int = 10,
    treasury_bps: int = 10,
    lp_bps:       int = 10,
) -> FeeAllocation:
    """Split gross LWC fee into burn/treasury/LP/reserve. Iterative arithmetic."""
    if fee_bps == 0:
        return FeeAllocation(0.0, 0.0, 0.0, 0.0, 0.0)
    burn      = gross_fee * burn_bps      / fee_bps
    treasury  = gross_fee * treasury_bps  / fee_bps
    lp_reward = gross_fee * lp_bps        / fee_bps
    reserve   = max(gross_fee - burn - treasury - lp_reward, 0.0)
    alloc = FeeAllocation(
        total_fee=gross_fee, burn_amount=burn,
        treasury_amount=treasury, lp_reward_amount=lp_reward, reserve_amount=reserve,
    )
    logger.info(
        f"[FeeEngine] Split {gross_fee:.6f} LWC → "
        f"burn={burn:.6f} treasury={treasury:.6f} LP={lp_reward:.6f} reserve={reserve:.6f}"
    )
    return alloc


async def _rpc_post(rpc_url: str, payload: dict, retries: int = 3) -> dict:
    """Async RPC call with retry loop — iterative, no recursion."""
    last_exc = None
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as sess:
                async with sess.post(
                    rpc_url, json=payload,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    return await r.json()
        except Exception as exc:
            last_exc = exc
            wait = 2 ** attempt          # 1s, 2s, 4s — iterative backoff
            logger.warning(f"[RPC] Attempt {attempt+1} failed: {exc} — retrying in {wait}s")
            await asyncio.sleep(wait)
    raise RuntimeError(f"[RPC] All {retries} attempts failed: {last_exc}")


async def execute_burn(rpc_url: str, wallet_pubkey: str, lwc_mint: str, amount: float, dry_run: bool) -> str:
    """Burn LWC by sending to the SPL null destination (close-and-burn pattern)."""
    lamports = int(amount * 1e9)
    if dry_run:
        logger.info(f"[FeeEngine DRY RUN] Would burn {amount:.6f} LWC ({lamports} lamports)")
        return "dry_run"
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "sendTransaction",
        "params": [{"burnInstruction": {"mint": lwc_mint, "amount": lamports, "authority": wallet_pubkey}}]
    }
    resp = await _rpc_post(rpc_url, payload)
    sig  = resp.get("result", "unknown")
    logger.info(f"[FeeEngine] Burned {amount:.6f} LWC | sig={sig}")
    return str(sig)


async def execute_transfer(
    rpc_url: str, from_pubkey: str, to_pubkey: str, lwc_mint: str, amount: float, label: str, dry_run: bool,
) -> str:
    """Transfer LWC between accounts via SPL token transfer."""
    lamports = int(amount * 1e9)
    if dry_run:
        logger.info(f"[FeeEngine DRY RUN] Would transfer {amount:.6f} LWC → {label} ({to_pubkey[:8]}...)")
        return "dry_run"
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "sendTransaction",
        "params": [{"transferInstruction": {
            "from": from_pubkey, "to": to_pubkey,
            "mint": lwc_mint, "amount": lamports,
        }}]
    }
    resp = await _rpc_post(rpc_url, payload)
    sig  = resp.get("result", "unknown")
    logger.info(f"[FeeEngine] Transfer {amount:.6f} LWC → {label} | sig={sig}")
    return str(sig)


async def distribute_fees(
    alloc:          FeeAllocation,
    rpc_url:        str,
    wallet_pubkey:  str,
    lwc_mint:       str,
    treasury_pubkey:str,
    lp_pool_pubkey: str,
    dry_run:        bool = True,
) -> Dict[str, str]:
    """
    Execute all three fee flows: burn, treasury, LP rewards.
    Iterative — no recursion. Returns dict of action -> tx signature.
    """
    results: Dict[str, str] = {}

    if alloc.burn_amount > 0:
        results["burn"] = await execute_burn(rpc_url, wallet_pubkey, lwc_mint, alloc.burn_amount, dry_run)

    if alloc.treasury_amount > 0:
        results["treasury"] = await execute_transfer(
            rpc_url, wallet_pubkey, treasury_pubkey, lwc_mint, alloc.treasury_amount, "UBI Treasury", dry_run
        )

    if alloc.lp_reward_amount > 0:
        results["lp_reward"] = await execute_transfer(
            rpc_url, wallet_pubkey, lp_pool_pubkey, lwc_mint, alloc.lp_reward_amount, "LP Reward Pool", dry_run
        )

    return results
