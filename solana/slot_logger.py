#!/usr/bin/env python3
"""
Slot Logger — Async Solana slot tracking with structured JSON output for LWC ecosystem audit trail.
Repo: lwc-utility-token | Author: Richard Patterson (@De-ASI-INTERFACE)
"""

import asyncio
import logging
import time
import os
from solana.rpc_client import SolanaRPCClient

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "msg": "%(message)s"}'
)
logger = logging.getLogger("lwc.slot_logger")

LOG_INTERVAL = int(os.getenv("SLOT_LOG_INTERVAL", 10))


async def run_slot_logger():
    client = SolanaRPCClient()
    logger.info("Slot logger started")
    try:
        while True:
            try:
                slot = await client.get_slot("processed")
                confirmed = await client.get_slot("confirmed")
                epoch = await client.get_epoch_info()
                logger.info(
                    f"slot={slot} confirmed={confirmed} lag={slot - confirmed} "
                    f"epoch={epoch.get('epoch', 'N/A')}"
                )
            except Exception as e:
                logger.error(f"Slot log error: {e}")
            await asyncio.sleep(LOG_INTERVAL)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run_slot_logger())
