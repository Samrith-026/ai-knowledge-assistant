import logging
import os
import time

from app.redis_client import redis_client


logger = logging.getLogger(__name__)


RATE_LIMIT_REQUESTS = int(
    os.getenv("RATE_LIMIT_REQUESTS", "10")
)

RATE_LIMIT_WINDOW_SECONDS = int(
    os.getenv(
        "RATE_LIMIT_WINDOW_SECONDS",
        "60"
    )
)


def is_rate_limited(client_id: str) -> bool:

    current_window = (
        int(time.time())
        // RATE_LIMIT_WINDOW_SECONDS
    )

    key = (
        f"rate_limit:"
        f"{client_id}:"
        f"{current_window}"
    )

    try:

        count = redis_client.incr(key)

        if count == 1:

            redis_client.expire(
                key,
                RATE_LIMIT_WINDOW_SECONDS
            )

        logger.info(
            "Rate limit count client=%s count=%d",
            client_id,
            count
        )

        return count > RATE_LIMIT_REQUESTS

    except Exception:

        logger.exception(
            "Redis rate-limit check failed"
        )

        # Fail open if Redis is unavailable.
        return False