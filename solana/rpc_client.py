#!/usr/bin/env python3
"""
Solana RPC Client — Low-latency async wrapper for LWC Utility Token ecosystem.
Features: persistent TCPConnector session, hard timeouts, connection pooling, DNS cache.
Repo: lwc-utility-token | Author: Richard Patterson (@De-ASI-INTERFACE)
"""

import logging
import os
from typing import Any, Optional

import aiohttp

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
)
logger = logging.getLogger("lwc.rpc")

SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
_RPC_TIMEOUT = aiohttp.ClientTimeout(total=4, connect=1)


class SolanaRPCClient:
    """
    Async Solana RPC client with persistent connection pool for minimum per-call overhead.
    Use as async context manager or call close() explicitly.
    """

    def __init__(self, rpc_url: str = SOLANA_RPC_URL):
        self.rpc_url = rpc_url
        self._connector: Optional[aiohttp.TCPConnector] = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._connector = aiohttp.TCPConnector(
                limit=20,
                ttl_dns_cache=600,
                enable_cleanup_closed=True
            )
            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=_RPC_TIMEOUT
            )
        return self._session

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, *_):
        await self.close()

    async def _post(self, method: str, params: list) -> Any:
        session = await self._ensure_session()
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        async with session.post(self.rpc_url, json=payload) as resp:
            data = await resp.json(content_type=None)
            return data.get("result", {})

    async def get_slot(self, commitment: str = "processed") -> int:
        result = await self._post("getSlot", [{"commitment": commitment}])
        return result if isinstance(result, int) else 0

    async def get_token_supply(self, mint_address: str) -> dict:
        result = await self._post("getTokenSupply", [mint_address])
        return result.get("value", {}) if isinstance(result, dict) else {}

    async def get_account_info(self, pubkey: str, encoding: str = "jsonParsed") -> dict:
        return await self._post("getAccountInfo", [pubkey, {"encoding": encoding}])

    async def get_epoch_info(self) -> dict:
        result = await self._post("getEpochInfo", [])
        return result if isinstance(result, dict) else {}

    async def get_balance(self, pubkey: str) -> int:
        result = await self._post("getBalance", [pubkey])
        return result.get("value", 0) if isinstance(result, dict) else 0
