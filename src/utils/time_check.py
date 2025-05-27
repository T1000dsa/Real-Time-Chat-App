import time
import logging
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

def time_checker(func):
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 10**3
        log_time(elapsed_ms, func.__name__)
        return result

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        end = time.perf_counter()
        elapsed_ms = (end - start) * 10**3
        log_time(elapsed_ms, func.__name__)
        return result

    def log_time(elapsed_ms: float, func_name: str):
        if func_name == 'refresh_token':
            logger.debug(f'Request time spent: {elapsed_ms:.4f} ms.')
        else:
            logger.debug(f'Time spent: {elapsed_ms:.4f} ms. Func: {func_name}')

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper