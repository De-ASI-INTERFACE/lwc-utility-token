#!/usr/bin/env python3
"""
Solana RPC Client — Async wrapper for LWC Utility Token ecosystem.
Handles slot fetching, account info, supply queries for AMM/staking/market-making modules.
Repo: lwc-utility-token | Author: Richard Patterson (@De-ASI-INTERFACE)
"""

import aiohttp
import logging
import os
import time
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
)
logger = logging.getLogger("lwc.rpc")

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
LWC_MINT_ADDRESS = os.getenv("LWC_MINT_ADDRESS", "")


class SolanaRPCClient:
    def __init__(self, rpc_url: str = SOLANA_RPC_URL):
        self.rpc_url = rpc_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def _post(self, method: str, params: list) -> dict:
        session = await self._get_session()
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with session.post(self.rpc_url, json=payload) as resp:
            data = await resp.json()
            return data.get("result", {})

    async def get_slot(self, commitment: str = "processed") -> int:
        result = await self._post("getSlot", [{"commitment": commitment}])
        return result if isinstance(result, int) else 0

    async def get_token_supply(self, mint_address: str) -> dict:
        """Fetch SPL token supply for LWC mint — used by AMM, staking, market-making modules."""
        result = await self._post("getTokenSupply", [mint_address])
        return result.get("value", {})

    async def get_account_info(self, pubkey: str, encoding: str = "jsonParsed") -> dict:
        result = await self._post("getAccountInfo", [pubkey, {"encoding": encoding}])
        return result

    async def get_epoch_info(self) -> dict:
        return await self._post("getEpochInfo", [])

    async def get_balance(self, pubkey: str) -> int:
        result = await self._post("getBalance", [pubkey])
        return result.get("value", 0) if isinstance(result, dict) else 0
