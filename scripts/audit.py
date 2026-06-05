#!/usr/bin/env python3
"""
LWC Utility Token Audit — Solana production-readiness scanner.
Creator: Richard Patterson (@De-ASI-INTERFACE)
"""
from __future__ import annotations
import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Finding:
    rule_id: str
    severity: str
    file: str
    line: int
    title: str
    detail: str
    remediation: str
    penalty: int


RULES = [
    {"id": "RPC-001", "sev": "CRITICAL", "penalty": 18,
     "import_missing": ["SolanaRPCClient", "rpc_client", "AsyncClient"],
     "title": "No Solana RPC client",
     "detail": "No on-chain interaction layer found.",
     "remediation": "Use SolanaRPCClient from token/rpc_client.py."},
    {"id": "LOG-001", "sev": "CRITICAL", "penalty": 12,
     "log_missing": "slot",
     "title": "No slot in logs",
     "detail": "Token events not anchored to Solana slot time.",
     "remediation": "Use TokenSlotLogger for all on-chain events."},
    {"id": "LOG-002", "sev": "HIGH", "penalty": 8,
     "log_missing": "confirmation_level",
     "title": "No confirmation_level in logs",
     "detail": "Cannot audit processed/confirmed/finalized state.",
     "remediation": "Add confirmation_level to all token event logs."},
    {"id": "CACHE-001", "sev": "CRITICAL", "penalty": 12,
     "import_missing": ["redis", "aioredis"],
     "title": "No Redis state cache",
     "detail": "Staking and MM state lost on process exit.",
     "remediation": "Use RedisStakingState and RedisMMState."},
    {"id": "CACHE-002", "sev": "HIGH", "penalty": 8,
     "import_missing": ["RedisTokenState", "redis_token_state"],
     "title": "No Redis token supply cache",
     "detail": "Supply read from RPC on every call, adding 50-200ms per read.",
     "remediation": "Cache supply via RedisTokenState with 10s TTL."},
    {"id": "ASYNC-001", "sev": "HIGH", "penalty": 10,
     "pattern": r"time\.sleep",
     "title": "Blocking sleep detected",
     "detail": "Synchronous sleep blocks event loop.",
     "remediation": "Replace with asyncio.sleep()."},
    {"id": "MM-001", "sev": "MEDIUM", "penalty": 6,
     "import_missing": ["RedisMMState", "redis_mm_state"],
     "title": "No crash-safe MM order state",
     "detail": "Open MM orders lost on crash = uncovered inventory.",
     "remediation": "Use RedisMMState to persist all active orders."},
]


def run_audit(root: Path) -> list[Finding]:
    py_files = list(root.rglob("*.py"))
    all_content = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in py_files)
    findings, seen = [], set()
    for rule in RULES:
        if rule["id"] in seen:
            continue
        hit = False
        if "pattern" in rule:
            for fp in py_files:
                lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
                for i, line in enumerate(lines, 1):
                    if re.search(rule["pattern"], line):
                        findings.append(Finding(rule_id=rule["id"], severity=rule["sev"],
                            file=str(fp), line=i, title=rule["title"],
                            detail=rule["detail"], remediation=rule["remediation"],
                            penalty=rule["penalty"]))
                        hit = True
                        break
                if hit:
                    break
        if not hit:
            for key in ("import_missing", "log_missing"):
                if key in rule:
                    kws = rule[key] if isinstance(rule[key], list) else [rule[key]]
                    if not any(kw in all_content for kw in kws):
                        findings.append(Finding(rule_id=rule["id"], severity=rule["sev"],
                            file="(global)", line=0, title=rule["title"],
                            detail=rule["detail"], remediation=rule["remediation"],
                            penalty=rule["penalty"]))
        seen.add(rule["id"])
    return findings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".")
    parser.add_argument("--output", default="reports/audit.md")
    args = parser.parse_args()
    findings = run_audit(Path(args.path))
    score = max(0, 100 - sum(f.penalty for f in findings))
    lines = [f"# LWC Token Audit\n**Score:** {score}/100\n**Findings:** {len(findings)}\n",
             "| Rule | Severity | File | Title | Penalty |",
             "|------|----------|------|-------|---------|",
             *[f"| {f.rule_id} | {f.severity} | `{f.file}` | {f.title} | -{f.penalty} |" for f in findings]]
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text("\n".join(lines))
    print("\n".join(lines))
    sys.exit(0 if score >= 70 else 1)


if __name__ == "__main__":
    main()
