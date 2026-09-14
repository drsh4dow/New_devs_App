import json
import os

import redis.asyncio as redis

from app.services.reservations import calculate_total_revenue

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))


async def get_revenue_summary(
    property_id: str,
    tenant_id: str,
    month: int | None = None,
    year: int | None = None,
) -> dict:
    # The new namespace excludes old, unscoped results (including sample totals).
    cache_key = "revenue:v2:" + json.dumps([tenant_id, property_id, year, month])
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    result = await calculate_total_revenue(property_id, tenant_id, month, year)
    await redis_client.setex(cache_key, 300, json.dumps(result))
    return result
