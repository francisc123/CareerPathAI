"""
Startup-retry helpers shared by every Python service that connects to
Kafka, Redis, Postgres or Qdrant at boot.

USAGE (drop this file into each service's src/ as `retry.py`):

    from .retry import startup_retry

    @startup_retry("kafka")
    async def start_consumer():
        consumer = AIOKafkaConsumer(...)
        await consumer.start()
        return consumer

    @startup_retry("redis")
    async def open_redis():
        client = redis.from_url(REDIS_URL, decode_responses=True)
        await client.ping()
        return client

Why this matters
----------------
`depends_on: condition: service_healthy` only guarantees the backend's
healthcheck has passed at least once. Kafka in particular keeps rebalancing
its consumer groups for several seconds after `rpk cluster health` reports
healthy, and a service that crashes during that window will be restarted by
Docker — but its consumer-group offsets may already be committed in a bad
state. A few seconds of retry at startup turns a flaky cold start into a
predictable one.
"""
import logging
from functools import wraps

from tenacity import (
    AsyncRetrying,
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
    before_sleep_log,
)

# Each backend gets its own envelope so we can tune timing per-dependency
# without writing four near-identical decorators.
_PROFILES = {
    "kafka":    {"max_wait_s": 90, "min_backoff_s": 1, "max_backoff_s": 8},
    "redis":    {"max_wait_s": 30, "min_backoff_s": 0.5, "max_backoff_s": 4},
    "postgres": {"max_wait_s": 60, "min_backoff_s": 1, "max_backoff_s": 5},
    "qdrant":   {"max_wait_s": 60, "min_backoff_s": 1, "max_backoff_s": 5},
}

logger = logging.getLogger(__name__)


def startup_retry(backend: str):
    """
    Decorator that retries an async function on any exception, with
    exponential backoff, until it succeeds or the per-backend deadline passes.
    """
    if backend not in _PROFILES:
        raise ValueError(f"Unknown backend {backend!r}; use one of {list(_PROFILES)}")
    cfg = _PROFILES[backend]

    def decorator(fn):
        @wraps(fn)
        async def wrapped(*args, **kwargs):
            async for attempt in AsyncRetrying(
                    stop=stop_after_delay(cfg["max_wait_s"]),
                    wait=wait_exponential(
                        multiplier=cfg["min_backoff_s"],
                        max=cfg["max_backoff_s"],
                    ),
                    retry=retry_if_exception_type(Exception),
                    before_sleep=before_sleep_log(logger, logging.WARNING),
                    reraise=True,
            ):
                with attempt:
                    logger.info(
                        "Connecting to %s (attempt %d)…",
                        backend,
                        attempt.retry_state.attempt_number,
                    )
                    result = await fn(*args, **kwargs)
                    logger.info("Connected to %s.", backend)
                    return result
        return wrapped

    return decorator