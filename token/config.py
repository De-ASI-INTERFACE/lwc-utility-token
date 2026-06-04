"""LWC Token Configuration

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
"""
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED = ["SOLANA_PRIVATE_KEY", "RPC_URL", "LWC_MINT_ADDRESS", "UBI_TREASURY_PUBKEY"]


def validate_env() -> None:
    missing = [k for k in REQUIRED if not os.getenv(k)]
    if missing:
        raise EnvironmentError(f"[LWC Config] Missing env vars: {missing}")


class LWCConfig:
    """All LWC token environment settings."""

    def __init__(self):
        validate_env()
        self.rpc_url: str        = os.getenv("RPC_URL")
        self.rpc_backup: str     = os.getenv("RPC_URL_BACKUP", "")
        self.private_key: str    = os.getenv("SOLANA_PRIVATE_KEY")
        self.lwc_mint: str       = os.getenv("LWC_MINT_ADDRESS")
        self.treasury: str       = os.getenv("UBI_TREASURY_PUBKEY")
        self.dry_run: bool       = os.getenv("DRY_RUN", "true").lower() == "true"
        self.jupiter_url: str    = os.getenv("JUPITER_API_URL", "https://quote-api.jup.ag/v6")
        self.deasi_api: str      = os.getenv("DEASI_API_URL", "https://api.deasi.io")
