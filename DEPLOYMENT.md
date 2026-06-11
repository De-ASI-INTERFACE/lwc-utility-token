# lwc-utility-token — Production Deployment Guide

## Railway Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LWC_MINT_ADDRESS` | ✅ | LWC SPL token mint address on Solana mainnet |
| `SOLANA_RPC_URL` | ✅ | Solana mainnet RPC endpoint |
| `REDIS_URL` | ✅ | Redis connection URL |
| `SUPPLY_CACHE_TTL` | optional | Redis key TTL in seconds (default: 30) |
| `SUPPLY_REFRESH_INTERVAL` | optional | Cache refresh interval in seconds (default: 15) |
| `SLOT_LOG_INTERVAL` | optional | Slot logger interval in seconds (default: 10) |

## CircleCI Environment Variables

- `SOLANA_RPC_URL`
- `REDIS_URL`
- `LWC_MINT_ADDRESS`

## Redis Key Schema

| Key | TTL | Consumer |
|---|---|---|
| `lwc:supply:amm` | 30s | AMM fee integration module |
| `lwc:supply:staking` | 30s | Staking rewards module |
| `lwc:supply:marketmaking` | 30s | Market-making module |

## Deploy Commands

```bash
# Start supply cache
python -m cache.redis_supply_cache

# Start slot logger
python -m solana.slot_logger
```

## Latency Profile

- RPC client pool: 20 connections, 600s DNS cache
- Hard RPC timeout: 4s
- Supply cache refresh: 15s cycle
