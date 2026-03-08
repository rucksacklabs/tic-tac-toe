from re import A
import time

from fastapi import APIRouter, Depends, HTTPException
from app.models import Game, Move

from app.persistence.game_repository import GameRepository
from app.persistence.schemas import (
    AICoachResponse,
    GameResponse,
    MoveHistoryItem,
    MoveRequest,
    MoveResponse,
    CoachStatusResonse,
)
from app.dependency_injection import (
    get_ai_coach,
    get_metrics,
    get_game_repo,
    get_openai_client,
)
from app.services.ai_coach import AICoach, AICoachError
from app.metrics.protocol import MetricsClient
from app.environment import Environment


router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/status", response_model=CoachStatusResonse)
async def coach_status() -> CoachStatusResonse:
    if not Environment.OPENAI_API_KEY_ENV:
        return CoachStatusResonse(
            available=False,
            message="Game coach not available, please configure OPENAI_API_KEY",
        )
    try:
        coach = get_ai_coach(get_openai_client())
        status = await coach.status()
        return CoachStatusResonse(available=status.ready, message=status.message)
    except Exception as e:
        return CoachStatusResonse(
            available=False, message=f"AI coach not available: {e}"
        )


@router.get("/{game_id}", response_model=AICoachResponse)
async def coach_game(
    game_id: str,
    repo: GameRepository = Depends(get_game_repo),
    coach: AICoach = Depends(get_ai_coach),
    metrics: MetricsClient = Depends(get_metrics),
) -> AICoachResponse:
    game = await repo.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=409, detail=f"Game is already {game.status}")

    metrics.increment("ai_coach.request")
    start = time.monotonic()
    try:
        recommended_position, message = await coach.get_ai_coach_recommendation(game)
    except AICoachError as e:
        metrics.increment("ai_coach.error", tags={"error_type": type(e).__name__})
        raise HTTPException(status_code=502, detail=str(e))

    duration_ms = (time.monotonic() - start) * 1000
    metrics.timing("ai_coach.duration_ms", duration_ms)

    recommended_x = recommended_position % 3
    recommended_y = recommended_position // 3
    return AICoachResponse(
        game=GameResponse.model_validate(game),
        recommended_x=recommended_x,
        recommended_y=recommended_y,
        message=message,
    )
