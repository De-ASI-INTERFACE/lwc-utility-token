"""LWC Market Making Engine — Jupiter routing integration.
Iterative order management. No recursion.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Deque
import aiohttp
from loguru import logger

JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"


@dataclass
class MMOrder:
    side: str  # 'buy' | 'sell'
    input_mint: str
    output_mint: str
    amount: int  # lamports / raw units
    slippage_bps: int = 50
    created_at: float = 0.0

    def __post_init__(self) -> None:
        self.created_at = time.time()


class MarketMaker:
    """Submits and tracks LWC buy/sell orders via Jupiter."""

    def __init__(self, lwc_mint: str, sol_mint: str = "So11111111111111111111111111111111111111112") -> None:
        self.lwc_mint = lwc_mint
        self.sol_mint = sol_mint
        self._order_history: Deque[MMOrder] = deque(maxlen=5_000)

    async def get_quote(self, input_mint: str, output_mint: str, amount: int, slippage_bps: int = 50) -> dict:
        """Fetch a Jupiter swap quote."""
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": slippage_bps,
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(JUPITER_QUOTE_URL, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Jupiter quote failed: {resp.status}")
                    return {}
                return await resp.json()

    async def place_buy(self, amount_lamports: int) -> dict:
        order = MMOrder(side="buy", input_mint=self.sol_mint, output_mint=self.lwc_mint, amount=amount_lamports)
        self._order_history.append(order)
        quote = await self.get_quote(self.sol_mint, self.lwc_mint, amount_lamports)
        logger.info(f"BUY order placed: {amount_lamports} lamports")
        return quote

    async def place_sell(self, amount_raw: int) -> dict:
        order = MMOrder(side="sell", input_mint=self.lwc_mint, output_mint=self.sol_mint, amount=amount_raw)
        self._order_history.append(order)
        quote = await self.get_quote(self.lwc_mint, self.sol_mint, amount_raw)
        logger.info(f"SELL order placed: {amount_raw} raw units")
        return quote

    def recent_orders(self, n: int = 20) -> list[MMOrder]:
        result: list[MMOrder] = []
        for i, order in enumerate(self._order_history):
            if i >= n:
                break
            result.append(order)
        return result
