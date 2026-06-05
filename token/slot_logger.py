"""
Slot-Aware Logger — token, staking, and MM events.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations
import sys
import time
from typing import Optional

from loguru import logger


def configure_logging(log_file: str = "logs/lwc_token_events.jsonl") -> None:
    logger.remove()
    logger.add(sys.stderr, level="INFO", format="{time} | {level} | {message}")
    logger.add(log_file, level="DEBUG", serialize=True,
               rotation="100 MB", retention="30 days", compression="gz")


class TokenSlotLogger:
    def __init__(self, component: str = "lwc-utility-token") -> None:
        self._component = component

    def transfer(self, *, slot: int, from_pk: str, to_pk: str, amount: float,
                 tx_sig: str, confirmation_level: str = "confirmed") -> None:
        logger.info("token_transfer", extra={
            "component": self._component, "slot": slot,
            "from": from_pk[:16], "to": to_pk[:16],
            "amount": amount, "tx_sig": tx_sig,
            "confirmation_level": confirmation_level,
            "ts_ms": int(time.time() * 1000),
        })

    def stake(self, *, slot: int, pubkey: str, amount: float,
              unlock_slot: int, tx_sig: str) -> None:
        logger.info("token_staked", extra={
            "component": self._component, "slot": slot,
            "pubkey": pubkey[:16], "amount": amount,
            "unlock_slot": unlock_slot, "tx_sig": tx_sig,
            "confirmation_level": "confirmed",
            "ts_ms": int(time.time() * 1000),
        })

    def governance_vote(self, *, slot: int, pubkey: str, proposal_id: str,
                        vote: str, weight: float, tx_sig: str) -> None:
        logger.info("governance_vote", extra={
            "component": self._component, "slot": slot,
            "pubkey": pubkey[:16], "proposal_id": proposal_id,
            "vote": vote, "weight": weight, "tx_sig": tx_sig,
            "confirmation_level": "finalized",
            "ts_ms": int(time.time() * 1000),
        })

    def mm_order(self, *, slot: int, order_id: str, symbol: str,
                 side: str, price: float, qty: float,
                 confirmation_level: str = "processed") -> None:
        logger.info("mm_order", extra={
            "component": self._component, "slot": slot,
            "order_id": order_id, "symbol": symbol,
            "side": side, "price": price, "qty": qty,
            "confirmation_level": confirmation_level,
            "ts_ms": int(time.time() * 1000),
        })
