"""
Purpose: Dependency injection container and provider logic.
Architecture: Application Layer. Decouples service creation from endpoint logic.
Notes: Initializes Anthropic client and AICoach service.
"""

from functools import lru_cache

from fastapi import Depends
from anthropic import AsyncAnthropic

from app.services.ai_coach import AICoach
from app.environment import Environment
from app.metrics.protocol import MetricsClient
from app.metrics.noop import NoOpMetricsClient


@lru_cache
def get_metrics() -> MetricsClient:
    return NoOpMetricsClient()


@lru_cache
def get_anthropic_client() -> AsyncAnthropic:
    key = Environment.ANTHROPIC_API_KEY_ENV
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable is required")
    return AsyncAnthropic(api_key=key)


def get_ai_coach(client: AsyncAnthropic = Depends(get_anthropic_client)) -> AICoach:
    return AICoach(client)
