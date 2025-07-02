import logging

from src.core.services.cache.redis import manager as redis_manager
from src.core.config.config import settings


logger = logging.getLogger(__name__)

redis = redis_manager.redis

async def check_login_attempts(
        user_identifier, 
        max_attempts=settings.redis.cache_auth_attempts, 
        lockout_time=settings.redis.cache_time_auth
        ):
    key = f"login_attempts:{user_identifier}"

    attempts = await redis.incr(key)
    logger.debug(f"{key} attempts: {attempts}")
    
    # Set expiration if this is the first failed attempt
    if attempts == 1:
        await redis.expire(key, lockout_time)
    
    if attempts > max_attempts:
        return False  # Too many attempts
    return True, attempts  # Allowed to attempt login