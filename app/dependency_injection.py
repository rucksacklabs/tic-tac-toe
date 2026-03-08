"""
Purpose: Dependency injection container and provider logic.
Architecture: Application Layer. Decouples service creation from endpoint logic.
Notes: Initializes Anthropic client and AICoach service.
"""

from functools import lru_cache

from fastapi import Depends
from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_coach import AICoach
from app.environment import Environment
from app.metrics.protocol import MetricsClient
from app.metrics.noop import NoOpMetricsClient
from app.persistence.database import get_db
from app.persistence.sqlalchemy_game_repository import SqlAlchemyGameRepository


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


def get_game_repo(
    db: AsyncSession = Depends(get_db),
) -> SqlAlchemyGameRepository:
    return SqlAlchemyGameRepository(db)
