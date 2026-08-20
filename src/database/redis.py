import redis.asyncio as redis_async
"""Configure and expose the asynchronous Redis client."""
from src.conf.config import config

redis_client = redis_async.from_url(config.REDIS_URL, decode_responses=False)