"""LWC Utility Token — FastAPI server.
Exposes staking, governance, AMM fee, and market-making endpoints.
All handlers iterative. No recursion.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from staking.staking_engine import StakingEngine
from amm.fee_config import calculate_fee, batch_fee_summary
from governance.proposals import GovernanceManager

load_dotenv()

app = FastAPI(
    title="LWC Utility Token API",
    version="1.0.0",
    description="Staking, governance, AMM fee management for LWC SPL token",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

staking = StakingEngine()
governance = GovernanceManager()


# ---------- Models ----------
class StakeRequest(BaseModel):
    wallet: str
    amount: float
    lock_days: int = 0

class VoteRequest(BaseModel):
    proposal_id: str
    wallet: str
    amount: float
    support: bool

class FeeCalcRequest(BaseModel):
    amount: float
    tier: str = "standard"


# ---------- Health ----------
@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "lwc-api"}


# ---------- Staking ----------
@app.post("/staking/stake")
def stake(req: StakeRequest) -> dict:
    success = staking.stake(req.wallet, req.amount, req.lock_days)
    if not success:
        raise HTTPException(status_code=400, detail="Stake failed")
    return {"staked": req.amount, "wallet": req.wallet}

@app.post("/staking/unstake")
def unstake(wallet: str) -> dict:
    amount = staking.unstake(wallet)
    return {"unstaked": amount, "wallet": wallet}

@app.get("/staking/position/{wallet}")
def get_position(wallet: str) -> dict:
    pos = staking.get_position(wallet)
    if pos is None:
        raise HTTPException(status_code=404, detail="No stake found")
    return {"wallet": pos.wallet, "amount_lwc": pos.amount_lwc, "locked_until": pos.locked_until, "multiplier": pos.multiplier}

@app.get("/staking/total")
def total_staked() -> dict:
    return {"total_staked_lwc": staking.total_staked()}


# ---------- AMM Fees ----------
@app.post("/amm/fee")
def fee_calc(req: FeeCalcRequest) -> dict:
    return calculate_fee(req.amount, req.tier)


# ---------- Governance ----------
@app.post("/governance/vote")
def vote(req: VoteRequest) -> dict:
    success = governance.vote(req.proposal_id, req.wallet, req.amount, req.support)
    if not success:
        raise HTTPException(status_code=400, detail="Vote failed")
    return {"voted": True}

@app.get("/governance/finalize/{proposal_id}")
def finalize(proposal_id: str) -> dict:
    status = governance.finalize(proposal_id)
    return {"proposal_id": proposal_id, "status": status}
