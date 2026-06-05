import pytest
import json
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_refresh_supply_cache_writes_all_modules():
    """Verify supply cache writes to all three module keys: amm, staking, marketmaking."""
    from cache.redis_supply_cache import refresh_supply_cache, MODULE_KEYS

    mock_redis = AsyncMock()
    mock_rpc = AsyncMock()
    mock_rpc.get_token_supply = AsyncMock(return_value={
        "amount": "1000000000000",
        "decimals": 9,
        "uiAmount": 1000.0
    })
    mock_rpc.get_slot = AsyncMock(return_value=300000001)

    await refresh_supply_cache(mock_redis, mock_rpc)

    assert mock_redis.setex.call_count == len(MODULE_KEYS)
    called_keys = [call[0][0] for call in mock_redis.setex.call_args_list]
    for key in MODULE_KEYS.values():
        assert key in called_keys


@pytest.mark.asyncio
async def test_supply_payload_structure():
    """Validate cached payload contains required fields."""
    from cache.redis_supply_cache import refresh_supply_cache

    mock_redis = AsyncMock()
    mock_rpc = AsyncMock()
    mock_rpc.get_token_supply = AsyncMock(return_value={
        "amount": "500000000000",
        "decimals": 9,
        "uiAmount": 500.0
    })
    mock_rpc.get_slot = AsyncMock(return_value=300000002)

    await refresh_supply_cache(mock_redis, mock_rpc)

    _, call_args, _ = mock_redis.setex.call_args_list[0]
    payload = json.loads(mock_redis.setex.call_args_list[0][0][2])
    assert "amount" in payload
    assert "slot" in payload
    assert "uiAmount" in payload
