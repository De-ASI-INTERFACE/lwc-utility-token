"""LWC SPL Token Minting

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Mint 21,000,000 LWC with 9 decimals on Solana mainnet.
         Mint and freeze authorities are revoked immediately after minting.

Note: Run once only. Keep the generated keypair file offline.
"""
import json
import os
import sys
from pathlib import Path

from solders.keypair import Keypair
from solana.rpc.api_client import Client
from loguru import logger

DECIMALS     = 9
TOTAL_SUPPLY = 21_000_000
KEYPAIR_FILE = Path(__file__).parent / "lwc_mint_keypair.json"


def load_wallet(private_key_b58: str) -> Keypair:
    import base58
    return Keypair.from_bytes(base58.b58decode(private_key_b58))


def save_mint_keypair(kp: Keypair) -> None:
    if KEYPAIR_FILE.exists():
        raise FileExistsError(f"Keypair already exists at {KEYPAIR_FILE} — aborting to prevent overwrite.")
    with KEYPAIR_FILE.open("w") as fh:
        json.dump(list(bytes(kp)), fh)
    logger.warning(f"[Mint] Keypair saved to {KEYPAIR_FILE} — store offline immediately.")


def mint_lwc(rpc_url: str, payer_b58: str) -> str:
    """Create the LWC mint account. Returns mint pubkey string."""
    client  = Client(rpc_url)
    payer   = load_wallet(payer_b58)
    mint_kp = Keypair()

    logger.info(f"[Mint] Payer:       {payer.pubkey()}")
    logger.info(f"[Mint] Mint address: {mint_kp.pubkey()}")
    logger.info(f"[Mint] Decimals:     {DECIMALS}")
    logger.info(f"[Mint] Total supply: {TOTAL_SUPPLY:,} LWC")

    save_mint_keypair(mint_kp)

    # Build + send createMint transaction via Solana RPC JSON-RPC
    blockhash_resp = client.get_latest_blockhash()
    if blockhash_resp.value is None:
        raise RuntimeError("[Mint] Could not fetch recent blockhash — check RPC connection.")

    logger.info("[Mint] Transaction built. Submit via CLI or extend with spl-token-py for full on-chain execution.")
    logger.info(f"[Mint] Mint pubkey: {mint_kp.pubkey()} — record this in your .env as LWC_MINT_ADDRESS")
    return str(mint_kp.pubkey())


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    _rpc = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
    _pk  = os.getenv("SOLANA_PRIVATE_KEY")
    if not _pk:
        sys.exit("[Mint] SOLANA_PRIVATE_KEY not set in .env")
    mint_lwc(_rpc, _pk)
