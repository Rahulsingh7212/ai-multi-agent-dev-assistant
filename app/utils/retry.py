from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


# ============================
# RETRY DECORATORS
# ============================

# General retry — for any operation that might fail transiently
general_retry = retry(
    stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
    wait=wait_exponential(
        multiplier=1,
        min=settings.RETRY_WAIT_MIN,
        max=settings.RETRY_WAIT_MAX,
    ),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# LLM retry — for LLM API calls (rate limits, timeouts)
llm_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((
        ConnectionError,
        TimeoutError,
        Exception,  # Broad catch for LLM API errors
    )),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Redis retry — for Redis operations
redis_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)

# Tool retry — for tool executions
tool_retry = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, ValueError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)