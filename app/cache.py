import hashlib
import json
import logging
import os

from app.redis_client import redis_client


logger = logging.getLogger(__name__)


CACHE_TTL_SECONDS = int(
    os.getenv("CACHE_TTL_SECONDS", "300")
)


def build_cache_key(question: str) -> str:

    normalized_question = (
        question
        .strip()
        .lower()
    )

    question_hash = hashlib.sha256(
        normalized_question.encode("utf-8")
    ).hexdigest()

    return f"rag:answer:{question_hash}"


def get_cached_answer(question: str):

    key = build_cache_key(question)

    try:

        cached = redis_client.get(key)

        if cached:

            logger.info(
                "Cache HIT for question"
            )

            return json.loads(cached)

        logger.info(
            "Cache MISS for question"
        )

        return None

    except Exception:

        logger.exception(
            "Redis cache read failed"
        )

        return None


def cache_answer(
    question: str,
    result: dict
):

    key = build_cache_key(question)

    try:

        redis_client.setex(
            key,
            CACHE_TTL_SECONDS,
            json.dumps(result)
        )

        logger.info(
            "Answer cached for %d seconds",
            CACHE_TTL_SECONDS
        )

    except Exception:

        logger.exception(
            "Redis cache write failed"
        )