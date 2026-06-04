"""LWC On-Chain Governance — proposal and voting manager.
Fully iterative. Memory-safe deque event log.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque
from loguru import logger


class ProposalStatus(str, Enum):
    ACTIVE = "active"
    PASSED = "passed"
    FAILED = "failed"
    EXPIRED = "expired"


@dataclass
class Proposal:
    id: str
    title: str
    description: str
    proposer: str
    created_at: float = field(default_factory=time.time)
    expires_at: float = 0.0
    votes_for: float = 0.0
    votes_against: float = 0.0
    status: ProposalStatus = ProposalStatus.ACTIVE


class GovernanceManager:
    """Manage LWC governance proposals and votes."""

    QUORUM: float = 100_000.0   # 100K LWC minimum to pass
    VOTE_PERIOD: float = 7 * 86_400  # 7 days

    def __init__(self) -> None:
        self._proposals: dict[str, Proposal] = {}
        self._votes: dict[str, dict[str, float]] = {}  # proposal_id -> {wallet: amount}
        self._event_log: Deque[dict] = deque(maxlen=50_000)

    def create_proposal(self, proposal_id: str, title: str, description: str, proposer: str) -> Proposal:
        p = Proposal(
            id=proposal_id,
            title=title,
            description=description,
            proposer=proposer,
            expires_at=time.time() + self.VOTE_PERIOD,
        )
        self._proposals[proposal_id] = p
        self._votes[proposal_id] = {}
        self._event_log.append({"event": "proposal_created", "id": proposal_id, "ts": time.time()})
        logger.info(f"Proposal created: {title} ({proposal_id})")
        return p

    def vote(self, proposal_id: str, wallet: str, amount: float, support: bool) -> bool:
        proposal = self._proposals.get(proposal_id)
        if proposal is None or proposal.status != ProposalStatus.ACTIVE:
            logger.warning(f"Proposal {proposal_id} not active")
            return False
        if time.time() > proposal.expires_at:
            proposal.status = ProposalStatus.EXPIRED
            return False
        if wallet in self._votes[proposal_id]:
            logger.warning(f"{wallet} already voted on {proposal_id}")
            return False

        self._votes[proposal_id][wallet] = amount
        if support:
            proposal.votes_for += amount
        else:
            proposal.votes_against += amount

        self._event_log.append({"event": "vote", "proposal": proposal_id, "wallet": wallet, "support": support, "amount": amount, "ts": time.time()})
        logger.info(f"{wallet} voted {'FOR' if support else 'AGAINST'} {proposal_id}: {amount} LWC")
        return True

    def finalize(self, proposal_id: str) -> ProposalStatus:
        proposal = self._proposals.get(proposal_id)
        if proposal is None:
            return ProposalStatus.FAILED
        total = proposal.votes_for + proposal.votes_against
        if total < self.QUORUM:
            proposal.status = ProposalStatus.FAILED
        elif proposal.votes_for > proposal.votes_against:
            proposal.status = ProposalStatus.PASSED
        else:
            proposal.status = ProposalStatus.FAILED
        logger.info(f"Proposal {proposal_id} finalized: {proposal.status}")
        return proposal.status
