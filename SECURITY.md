# Security Policy

**Creator:** Richard Patterson (@De-ASI-INTERFACE)  
**Orgs:** @DeASI-INTERFACE · @QuantumTradingInfinity · @richy.ai

## Reporting a Vulnerability

Do NOT disclose publicly before we have had time to patch.

Send a report to: xyq4r5ndd9@privaterelay.appleid.com  
Include: description, reproduction steps, impact, suggested fix.

We respond within 48 hours.

## Security Architecture

- Mint authority: REVOKED — 21M fixed supply, no further minting possible
- Freeze authority: REVOKED — no account freezes possible
- LP tokens: locked 12+ months
- All secrets loaded from `.env` — never hardcoded
- No recursive code paths — all logic is iterative (eliminates stack overflow risk)
- Smart contract audit: planned Q3 2025

## Bug Bounty

| Severity | Bounty      |
|----------|-------------|
| Critical | 10,000 LWC  |
| High     | 5,000 LWC   |
| Medium   | 1,000 LWC   |
| Low      | 100 LWC     |
