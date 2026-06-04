"""Verify LWC On-Chain Supply and Authority Status

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Assert 21M supply, 9 decimals, and both authorities revoked.
         Run after minting and after any on-chain change for audit trail.
"""
import os
import sys

from solana.rpc.api_client import Client
from solders.pubkey import Pubkey
from loguru import logger

EXPECTED_SUPPLY   = 21_000_000
EXPECTED_DECIMALS = 9


def verify_supply(rpc_url: str, mint_address: str) -> dict:
    """Query on-chain mint account and assert LWC parameters. Returns status dict."""
    client = Client(rpc_url)
    mint   = Pubkey.from_string(mint_address)

    resp = client.get_account_info_json_parsed(mint)
    if resp.value is None:
        raise ValueError(f"[Verify] Mint account not found: {mint_address}")

    info     = resp.value.data.parsed["info"]
    supply   = int(info["supply"]) / (10 ** info["decimals"])
    decimals = info["decimals"]
    mint_auth   = info.get("mintAuthority")
    freeze_auth = info.get("freezeAuthority")

    checks = {
        "supply_ok":       supply == EXPECTED_SUPPLY,
        "decimals_ok":     decimals == EXPECTED_DECIMALS,
        "mint_revoked":    mint_auth is None,
        "freeze_revoked":  freeze_auth is None,
    }

    logger.info("[Verify] LWC on-chain status:")
    logger.info(f"  Supply:           {supply:,.0f} LWC  {'✓' if checks['supply_ok'] else '✗ MISMATCH'}")
    logger.info(f"  Decimals:         {decimals}           {'✓' if checks['decimals_ok'] else '✗ MISMATCH'}")
    logger.info(f"  Mint authority:   {'REVOKED ✓' if checks['mint_revoked'] else f'ACTIVE ✗ ({mint_auth})'}")
    logger.info(f"  Freeze authority: {'REVOKED ✓' if checks['freeze_revoked'] else f'ACTIVE ✗ ({freeze_auth})'}")

    failed = [k for k, v in checks.items() if not v]
    if failed:
        raise AssertionError(f"[Verify] Failed checks: {failed}")

    logger.success("[Verify] All LWC checks passed.")
    return checks


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    _rpc  = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
    _mint = os.getenv("LWC_MINT_ADDRESS")
    if not _mint:
        sys.exit("[Verify] LWC_MINT_ADDRESS not set in .env")
    verify_supply(_rpc, _mint)
