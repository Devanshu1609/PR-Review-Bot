"""Shared utilities for LLM retry/backoff (placeholder)."""
import time
import logging

logger = logging.getLogger(__name__)


def with_retry(func, *args, retries=3, backoff=1, **kwargs):
    last_exc = None
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exc = e
            logger.warning(f"LLM call failed (attempt {i+1}/{retries}): {e}")
            time.sleep(backoff * (2 ** i))
    raise last_exc
