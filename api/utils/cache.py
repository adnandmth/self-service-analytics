"""
Redis cache utilities for the chatbot
"""

import json
import asyncio
from typing import Any, Optional
from redis import asyncio as aioredis
import structlog

from api.core.config import settings

logger = structlog.get_logger()

# Redis connection pool
redis_pool = None

async def get_redis_pool():
    """Get Redis connection pool"""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_pool

async def get_cache(key: str) -> Optional[str]:
    """Get value from cache"""
    try:
        redis = await get_redis_pool()
        value = await redis.get(key)
        if value:
            logger.debug("Cache hit", key=key)
        return value
    except Exception as e:
        logger.warning("Cache get failed", key=key, error=str(e))
        return None

async def set_cache(key: str, value: str, expire: int = 3600) -> bool:
    """Set value in cache with expiration"""
    try:
        redis = await get_redis_pool()
        await redis.setex(key, expire, value)
        logger.debug("Cache set", key=key, expire=expire)
        return True
    except Exception as e:
        logger.warning("Cache set failed", key=key, error=str(e))
        return False

async def delete_cache(key: str) -> bool:
    """Delete value from cache"""
    try:
        redis = await get_redis_pool()
        await redis.delete(key)
        logger.debug("Cache deleted", key=key)
        return True
    except Exception as e:
        logger.warning("Cache delete failed", key=key, error=str(e))
        return False

async def get_cache_json(key: str) -> Optional[dict]:
    """Get JSON value from cache"""
    value = await get_cache(key)
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            logger.warning("Invalid JSON in cache", key=key)
            return None
    return None

async def set_cache_json(key: str, value: dict, expire: int = 3600) -> bool:
    """Set JSON value in cache"""
    try:
        json_value = json.dumps(value)
        return await set_cache(key, json_value, expire)
    except Exception as e:
        logger.warning("Cache JSON set failed", key=key, error=str(e))
        return False

async def cache_query_result(query_hash: str, result: dict, expire: int = 1800) -> bool:
    """Cache query result"""
    return await set_cache_json(f"query_result:{query_hash}", result, expire)

async def get_cached_query_result(query_hash: str) -> Optional[dict]:
    """Get cached query result"""
    return await get_cache_json(f"query_result:{query_hash}")

async def cache_sql_generation(query: str, sql: str, expire: int = 3600) -> bool:
    """Cache SQL generation result"""
    return await set_cache(f"sql_gen:{hash(query)}", sql, expire)

async def get_cached_sql_generation(query: str) -> Optional[str]:
    """Get cached SQL generation result"""
    return await get_cache(f"sql_gen:{hash(query)}")

async def increment_rate_limit(user_id: str) -> int:
    """Increment rate limit counter for user"""
    try:
        redis = await get_redis_pool()
        key = f"rate_limit:{user_id}"
        count = await redis.incr(key)
        await redis.expire(key, 60)  # Reset after 60 seconds
        return count
    except Exception as e:
        logger.warning("Rate limit increment failed", user_id=user_id, error=str(e))
        return 0

async def get_rate_limit_count(user_id: str) -> int:
    """Get current rate limit count for user"""
    try:
        redis = await get_redis_pool()
        key = f"rate_limit:{user_id}"
        count = await redis.get(key)
        return int(count) if count else 0
    except Exception as e:
        logger.warning("Rate limit get failed", user_id=user_id, error=str(e))
        return 0

async def clear_user_cache(user_id: str) -> bool:
    """Clear all cache entries for a user"""
    try:
        redis = await get_redis_pool()
        pattern = f"*:{user_id}"
        keys = await redis.keys(pattern)
        if keys:
            await redis.delete(*keys)
        logger.info("User cache cleared", user_id=user_id, keys_count=len(keys))
        return True
    except Exception as e:
        logger.warning("User cache clear failed", user_id=user_id, error=str(e))
        return False

async def get_cache_stats() -> dict:
    """Get cache statistics"""
    try:
        redis = await get_redis_pool()
        info = await redis.info()
        return {
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "0B"),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0)
        }
    except Exception as e:
        logger.warning("Cache stats failed", error=str(e))
        return {} 