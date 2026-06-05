# lwc-utility-token

LWC Utility Token — Solana SPL ecosystem layer with async RPC client, Redis supply caching for AMM/staking/market-making modules, slot logger, and CircleCI audit pipeline.

**Author:** Richard Patterson ([@De-ASI-INTERFACE](https://github.com/De-ASI-INTERFACE))

## Module Architecture

```
solana/
  rpc_client.py        ← Async Solana RPC wrapper (slot, supply, account, epoch)
  slot_logger.py       ← Continuous slot + lag logging
cache/
  redis_supply_cache.py ← LWC supply cache for amm / staking / marketmaking
tests/
  test_supply_cache.py  ← Async pytest suite
```

## Redis Keys

| Key | Module | TTL |
|-----|--------|-----|
| `lwc:supply:amm` | AMM fee integration | 30s |
| `lwc:supply:staking` | Staking rewards | 30s |
| `lwc:supply:marketmaking` | Market-making | 30s |

## Quick Start

```bash
cp .env.example .env
# Set LWC_MINT_ADDRESS to your SPL mint
pip install -r requirements.txt
python -m cache.redis_supply_cache
```

## CI

CircleCI runs `flake8`, `bandit`, `safety`, and `pytest` on every push to `Richy`.
