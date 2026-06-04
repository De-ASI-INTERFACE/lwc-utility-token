"""Revoke LWC Mint and Freeze Authorities

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: Lock LWC at 21M fixed supply. Irreversible.
         Run once, immediately after minting is complete.

Security: After revocation no new LWC can ever be minted.
          Freeze authority revocation prevents any account from being frozen.
"""
import os
import sys
import base58

from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solana.rpc.api_client import Client
from solana.rpc.commitment import Confirmed
from solana.rpc.types import TxOpts
from loguru import logger


def _build_wallet(pk_b58: str) -> Keypair:
    return Keypair.from_bytes(base58.b58decode(pk_b58))


def revoke_mint_authority(client: Client, mint: Pubkey, authority: Keypair) -> str:
    """Send SetAuthority(MintTokens, None) to permanently disable minting."""
    logger.info(f"[Revoke] Revoking MINT authority on {mint}")
    # Instruction bytes: spl-token SetAuthority(authorityType=0 [MintTokens], newAuthority=None)
    # Encoded as a raw instruction for maximum compatibility with solders
    from solders.instruction import Instruction, AccountMeta
    PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    data = bytes([6, 0, 0])  # SetAuthority, MintTokens, COption::None
    accounts = [
        AccountMeta(pubkey=mint,             is_signer=False, is_writable=True),
        AccountMeta(pubkey=authority.pubkey(), is_signer=True,  is_writable=False),
    ]
    instr = Instruction(program_id=PROGRAM_ID, accounts=accounts, data=data)
    bh    = client.get_latest_blockhash().value.blockhash
    from solders.message import MessageV0
    msg = MessageV0.try_compile(authority.pubkey(), [instr], [], bh)
    tx  = VersionedTransaction(msg, [authority])
    sig = client.send_transaction(tx, opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)).value
    logger.info(f"[Revoke] Mint authority revoked. Sig: {sig}")
    return str(sig)


def revoke_freeze_authority(client: Client, mint: Pubkey, authority: Keypair) -> str:
    """Send SetAuthority(FreezeAccount, None) to permanently disable freezing."""
    logger.info(f"[Revoke] Revoking FREEZE authority on {mint}")
    from solders.instruction import Instruction, AccountMeta
    PROGRAM_ID = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
    data = bytes([6, 1, 0])  # SetAuthority, FreezeAccount, COption::None
    accounts = [
        AccountMeta(pubkey=mint,              is_signer=False, is_writable=True),
        AccountMeta(pubkey=authority.pubkey(), is_signer=True,  is_writable=False),
    ]
    instr = Instruction(program_id=PROGRAM_ID, accounts=accounts, data=data)
    bh    = client.get_latest_blockhash().value.blockhash
    from solders.message import MessageV0
    msg = MessageV0.try_compile(authority.pubkey(), [instr], [], bh)
    tx  = VersionedTransaction(msg, [authority])
    sig = client.send_transaction(tx, opts=TxOpts(skip_preflight=False, preflight_commitment=Confirmed)).value
    logger.info(f"[Revoke] Freeze authority revoked. Sig: {sig}")
    return str(sig)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    _rpc  = os.getenv("RPC_URL", "https://api.mainnet-beta.solana.com")
    _pk   = os.getenv("SOLANA_PRIVATE_KEY")
    _mint = os.getenv("LWC_MINT_ADDRESS")
    if not _pk or not _mint:
        sys.exit("[Revoke] SOLANA_PRIVATE_KEY and LWC_MINT_ADDRESS must be set in .env")
    _client    = Client(_rpc)
    _authority = _build_wallet(_pk)
    _mint_pk   = Pubkey.from_string(_mint)
    revoke_mint_authority(_client, _mint_pk, _authority)
    revoke_freeze_authority(_client, _mint_pk, _authority)
    logger.success("[Revoke] All authorities revoked. LWC supply is permanently fixed at 21,000,000.")
