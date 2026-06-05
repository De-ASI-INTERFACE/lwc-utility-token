"""
Solana RPC Client — multi-endpoint with health checks and slot tracking.
Creator: Richard Patterson (@De-ASI-INTERFACE)

Shared across amm/, staking/, marketmaking/ modules.
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import aiohttp
from loguru import logger


@dataclass
class RPCEndpoint:
    url: str
    healthy: bool = True
    latency_ms: float = 0.0
    fail_count: int = 0


class SolanaRPCClient:
    """
    Lightweight multi-endpoint Solana RPC client.
    Routes all calls to the fastest healthy endpoint.
    """
    HEALTH_INTERVAL_S = 5.0
    MAX_FAIL_COUNT = 3

    def __init__(self, endpoints: list[str]) -> None:
        self._endpoints = [RPCEndpoint(url=u) for u in endpoints]
        self._session: Optional[aiohttp.ClientSession] = None
        self._best: Optional[RPCEndpoint] = None

    async def start(self) -> None:
        connector = aiohttp.TCPConnector(limit=50, keepalive_timeout=30)
        self._session = aiohttp.ClientSession(connector=connector)
        asyncio.create_task(self._health_loop())
        await self._check_all()
        logger.info("solana_rpc_client_started", extra={"endpoints": len(self._endpoints)})

    async def stop(self) -> None:
        if self._session:
            await self._session.close()

    async def _health_loop(self) -> None:
        while True:
            await asyncio.sleep(self.HEALTH_INTERVAL_S)
            await self._check_all()

    async def _check_all(self) -> None:
        await asyncio.gather(*[self._check(ep) for ep in self._endpoints], return_exceptions=True)
        healthy = [ep for ep in self._endpoints if ep.healthy]
        if healthy:
            self._best = min(healthy, key=lambda e: e.latency_ms)

    async def _check(self, ep: RPCEndpoint) -> None:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot", "params": []}
        t0 = time.perf_counter()
        try:
            async with self._session.post(ep.url, json=payload, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                data = await resp.json()
                ep.latency_ms = (time.perf_counter() - t0) * 1000
                ep.healthy = True
                ep.fail_count = 0
                logger.debug("rpc_health_ok", extra={
                    "url": ep.url[:40],
                    "latency_ms": round(ep.latency_ms, 2),
                    "slot": data.get("result"),
                })
        except Exception as exc:
            ep.fail_count += 1
            if ep.fail_count >= self.MAX_FAIL_COUNT:
                ep.healthy = False
                logger.warning("rpc_endpoint_demoted", extra={"url": ep.url[:40], "error": str(exc)})

    @property
    def active_url(self) -> str:
        if self._best and self._best.healthy:
            return self._best.url
        for ep in self._endpoints:
            if ep.healthy:
                return ep.url
        raise RuntimeError("No healthy Solana RPC endpoints available")

    async def get_slot(self, commitment: str = "confirmed") -> int:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot",
                   "params": [{"commitment": commitment}]}
        async with self._session.post(self.active_url, json=payload) as resp:
            data = await resp.json()
            return int(data["result"])

    async def get_token_supply(self, mint: str) -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenSupply",
                   "params": [mint, {"commitment": "confirmed"}]}
        async with self._session.post(self.active_url, json=payload) as resp:
            data = await resp.json()
            return data.get("result", {}).get("value", {})

    async def get_account_info(self, pubkey: str, commitment: str = "confirmed") -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
                   "params": [pubkey, {"encoding": "jsonParsed", "commitment": commitment}]}
        async with self._session.post(self.active_url, json=payload) as resp:
            data = await resp.json()
            return data.get("result", {})

    async def get_transaction(self, sig: str, commitment: str = "confirmed") -> dict:
        payload = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction",
                   "params": [sig, {"encoding": "jsonParsed", "commitment": commitment,
                                    "maxSupportedTransactionVersion": 0}]}
        async with self._session.post(self.active_url, json=payload) as resp:
            data = await resp.json()
            return data.get("result", {})
