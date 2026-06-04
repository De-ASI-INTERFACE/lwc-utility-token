"""LWC Governance Engine

Creator: Richard Patterson (@De-ASI-INTERFACE)
Orgs:    @DeASI-INTERFACE | @QuantumTradingInfinity | @richy.ai
Purpose: On-chain governance for LWC protocol parameters.
         1 staked LWC = 1 vote (time-weighted multipliers apply).

Design:
  - Iterative vote tallying and listing — no recursion anywhere
  - Flat proposal store with O(1) lookup by proposal_id
  - Generator-based listing for memory efficiency
  - 10% quorum required, simple majority to pass
"""
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Generator, List
from loguru import logger
from staking.staking_engine import get_power, total_voting_power


@dataclass
class Vote:
    voter:   str
    power:   float
    support: bool
    cast_at: float = field(default_factory=time.time)


@dataclass
class Proposal:
    proposal_id:     str
    proposer:        str
    title:           str
    description:     str
    parameter_key:   str
    new_value:       str
    voting_period_s: int        = 259_200
    created_at:      float      = field(default_factory=time.time)
    executed:        bool       = False
    votes:           List[Vote] = field(default_factory=list)
    _voted_wallets:  set        = field(default_factory=set)

    @property
    def expires_at(self) -> float:
        return self.created_at + self.voting_period_s

    @property
    def is_active(self) -> bool:
        return not self.executed and time.time() < self.expires_at

    def tally(self) -> tuple:
        """Iterative tally — no recursion. Returns (votes_for, votes_against)."""
        for_total     = 0.0
        against_total = 0.0
        for v in self.votes:
            if v.support:
                for_total += v.power
            else:
                against_total += v.power
        return for_total, against_total

    @property
    def participation_pct(self) -> float:
        tp = total_voting_power()
        if tp == 0:
            return 0.0
        f, a = self.tally()
        return (f + a) / tp * 100

    @property
    def passed(self) -> bool:
        if self.is_active:
            return False
        f, a = self.tally()
        return f > a and self.participation_pct >= 10.0


_PROPOSALS: Dict[str, Proposal] = {}
MIN_STAKE_TO_PROPOSE = 100.0


def submit_proposal(
    proposer:        str,
    title:           str,
    description:     str,
    parameter_key:   str,
    new_value:       str,
    voting_period_s: int   = 259_200,
    min_stake:       float = MIN_STAKE_TO_PROPOSE,
) -> Proposal:
    """Submit a governance proposal. Proposer must have >= min_stake voting power."""
    power = get_power(proposer)
    if power < min_stake:
        raise PermissionError(
            f"[Gov] {proposer[:8]}... has {power:.2f} power; min required: {min_stake}"
        )
    p = Proposal(
        proposal_id=str(uuid.uuid4()),
        proposer=proposer,
        title=title,
        description=description,
        parameter_key=parameter_key,
        new_value=new_value,
        voting_period_s=voting_period_s,
    )
    _PROPOSALS[p.proposal_id] = p
    logger.info(f"[Gov] Proposal '{title}' | id={p.proposal_id} | proposer={proposer[:8]}...")
    return p


def cast_vote(proposal_id: str, voter: str, support: bool) -> Vote:
    """Cast a vote. Weight = time-weighted staked LWC power. Dedup enforced."""
    p = _PROPOSALS.get(proposal_id)
    if p is None:
        raise KeyError(f"[Gov] Proposal {proposal_id} not found")
    if not p.is_active:
        raise PermissionError(f"[Gov] Proposal {proposal_id} is not active")
    if voter in p._voted_wallets:
        raise PermissionError(f"[Gov] {voter[:8]}... already voted")
    power = get_power(voter)
    if power == 0:
        raise PermissionError(f"[Gov] {voter[:8]}... has no staked LWC")
    v = Vote(voter=voter, power=power, support=support)
    p.votes.append(v)
    p._voted_wallets.add(voter)
    logger.info(
        f"[Gov] {voter[:8]}... voted {'FOR' if support else 'AGAINST'} "
        f"'{p.title}' power={power:.2f}"
    )
    return v


def proposal_status(proposal_id: str) -> dict:
    """Return full status snapshot of a proposal."""
    p = _PROPOSALS.get(proposal_id)
    if p is None:
        raise KeyError(f"[Gov] Proposal {proposal_id} not found")
    f, a = p.tally()
    return {
        "proposal_id":       p.proposal_id,
        "title":             p.title,
        "proposer":          p.proposer,
        "parameter_key":     p.parameter_key,
        "new_value":         p.new_value,
        "is_active":         p.is_active,
        "votes_for":         f,
        "votes_against":     a,
        "participation_pct": p.participation_pct,
        "passed":            p.passed,
        "executed":          p.executed,
        "expires_at":        p.expires_at,
        "total_votes":       len(p.votes),
    }


def list_proposals(active_only: bool = False) -> Generator[dict, None, None]:
    """Memory-safe generator over proposals. Use active_only=True to filter."""
    for p in _PROPOSALS.values():
        if active_only and not p.is_active:
            continue
        yield proposal_status(p.proposal_id)
