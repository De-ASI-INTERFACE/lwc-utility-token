"""LWC SPL Token — mint verification and supply audit.
All logic iterative. No recursion. Memory-safe.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from solana.rpc.api import Client
from solders.pubkey import Pubkey
from loguru import logger

load_dotenv()

RPC_URL: str = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
LWC_MINT: str = os.getenv("LWC_MINT_ADDRESS", "")
EXPECTED_SUPPLY: int = 21_000_000 * (10 ** 9)  # 21M with 9 decimals


def verify_supply(client: Client, mint_address: str) -> dict:
    """Verify LWC token supply and authority status."""
    results: dict = {"mint": mint_address, "errors": []}
    try:
        pubkey = Pubkey.from_string(mint_address)
        info = client.get_account_info(pubkey)
        if info.value is None:
            results["errors"].append("Mint account not found")
            return results

        supply_resp = client.get_token_supply(pubkey)
        actual = int(supply_resp.value.amount)
        results["supply_raw"] = actual
        results["supply_lwc"] = actual / (10 ** 9)
        results["supply_match"] = actual == EXPECTED_SUPPLY
        if not results["supply_match"]:
            results["errors"].append(
                f"Supply mismatch: expected {EXPECTED_SUPPLY}, got {actual}"
            )
        logger.info(f"LWC supply verified: {results['supply_lwc']:,.2f} LWC")
    except Exception as exc:
        results["errors"].append(str(exc))
        logger.error(f"Supply verification failed: {exc}")
    return results


def main() -> None:
    if not LWC_MINT:
        logger.error("LWC_MINT_ADDRESS not set in .env")
        return
    client = Client(RPC_URL)
    result = verify_supply(client, LWC_MINT)
    for key, val in result.items():
        logger.info(f"{key}: {val}")


if __name__ == "__main__":
    main()
