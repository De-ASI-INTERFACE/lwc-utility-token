# LWC Utility Token — Solana SPL

**Creator & Lead Architect:** Richard Patterson  
**GitHub:** [@De-ASI-INTERFACE](https://github.com/De-ASI-INTERFACE)  
**Orgs:** @DeASI-INTERFACE · @QuantumTradingInfinity · @richy.ai  
**Launch:** April 2025 — Solana Mainnet  

---

## What LWC Is

LWC is the native utility and governance token of the DeASI ecosystem.
It powers fee settlement, staking rewards, on-chain governance, API subscriptions,
and market-making across every layer of the RP SPL AMM Platform and DeASI AI infrastructure.

---

## Tokenomics

| Parameter         | Value                          |
|-------------------|--------------------------------|
| Name              | Linework Coin                  |
| Symbol            | LWC                            |
| Decimals          | 9                              |
| Total Supply      | 21,000,000 LWC                 |
| Mint Authority    | Revoked (fixed supply)         |
| Freeze Authority  | Revoked                        |
| Blockchain        | Solana (SPL)                   |

### Allocation

| Category               | %   | Amount (LWC)  | Vesting              |
|------------------------|-----|---------------|----------------------|
| Community / Ecosystem  | 35% | 7,350,000     | Immediate            |
| Liquidity / MM Reserve | 20% | 4,200,000     | Locked 12+ months    |
| Team & Advisors        | 15% | 3,150,000     | 24mo, 6mo cliff      |
| Public Sale            | 15% | 3,150,000     | Immediate            |
| Treasury / Dev Fund    | 15% | 3,150,000     | Governance-controlled|

---

## Utility Model

1. **AMM Fee Token** — All `rp_spl_amm_platform_v1` trading fees settled in LWC
2. **Staking Rewards** — Fee share + emissions for stakers and LPs
3. **Governance** — 1 LWC = 1 vote; time-weighted multipliers for locked positions
4. **API Access** — DeASI AI tiers gated by LWC stake/payment
5. **Buyback-and-Burn** — 30% of protocol revenue buys and burns LWC

---

## Repository Structure

```
lwc-utility-token/
├── token/           SPL mint, metadata, supply verification, authority revocation
├── amm/             AMM fee token configuration and integration helpers
├── staking/         Staking engine — memory-optimized, iterative
├── governance/      On-chain governance — proposals, voting, execution
├── api/             DeASI AI API subscription tier management
├── marketmaking/    LWC market-making bot integration (Jupiter routing)
├── dashboards/      Grafana dashboard configs for real-time monitoring
└── docs/            Whitepaper, audit notes, legal disclaimer
```

---

## Quick Start

```bash
git clone https://github.com/De-ASI-INTERFACE/lwc-utility-token
cd lwc-utility-token
pip install -r requirements.txt
cp .env.example .env  # fill in your values
python token/verify_supply.py
```

---

## Security

- Mint authority: REVOKED — supply permanently fixed at 21M
- Freeze authority: REVOKED — no account freezes possible
- LP tokens: locked 12+ months
- No recursive code — all logic is iterative and memory-safe
- All secrets via `.env` — never hardcoded

---

## License

MIT License — Copyright (c) 2025 Richard Patterson (@De-ASI-INTERFACE)
