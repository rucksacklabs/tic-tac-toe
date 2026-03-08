"""
Purpose: REST API endpoints for game management and moves.
Architecture: Presentation Layer (API).
Notes: Handles request validation, routes to business logic services, and persists changes.
"""

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
)
from app.services.game_service import (
    GameError,
    make_new_game,
    play_turn_vs_computer_with_trace,
)
from app.dependency_injection import get_ai_coach, get_metrics, get_game_repo
from app.services.ai_coach import AICoach, AICoachError
from app.metrics.protocol import MetricsClient

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", status_code=201)
async def create_game(
    repo: GameRepository = Depends(get_game_repo),
    metrics: MetricsClient = Depends(get_metrics),
) -> GameResponse:
    game = await repo.create(make_new_game())
    metrics.increment("game.created")
    return game


@router.get("/{game_id}")
async def get_game(
    game_id: str,
    repo: GameRepository = Depends(get_game_repo),
) -> GameResponse:
    game = await repo.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("")
async def list_games(
    repo: GameRepository = Depends(get_game_repo),
) -> list[GameResponse]:
    return await repo.list_all()


@router.post("/{game_id}/moves")
async def make_move(
    game_id: str,
    move: MoveRequest,
    repo: GameRepository = Depends(get_game_repo),
    metrics: MetricsClient = Depends(get_metrics),
) -> MoveResponse:
    game = await repo.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=409, detail=f"Game is already {game.status}")

    try:
        message, applied_moves = play_turn_vs_computer_with_trace(game, move.x, move.y)
    except GameError as e:
        raise HTTPException(status_code=422, detail=str(e))

    move_count = await repo.count_moves(game_id)
    next_move_number = move_count + 1

    moves_to_add = []
    for player, move_x, move_y in applied_moves:
        moves_to_add.append(
            {
                "move_number": next_move_number,
                "player": player,
                "x": move_x,
                "y": move_y,
            }
        )
        next_move_number += 1

    await repo.add_moves(game_id, moves_to_add)
    game = await repo.save(game)

    if game.status == "won":
        outcome = f"{game.winner.lower()}_wins" if game.winner else "none"
    elif game.status == "draw":
        outcome = "draw"
    else:
        outcome = "none"
    metrics.increment("game.move", tags={"outcome": outcome})

    response_data = GameResponse.model_validate(game).model_dump()
    response_data["message"] = message
    return MoveResponse(**response_data)


@router.get("/{game_id}/moves", response_model=list[MoveHistoryItem])
async def list_game_moves(
    game_id: str,
    repo: GameRepository = Depends(get_game_repo),
):
    game = await repo.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return await repo.get_moves(game_id)


@router.delete("/{game_id}", status_code=204)
async def delete_game(
    game_id: str,
    repo: GameRepository = Depends(get_game_repo),
    metrics: MetricsClient = Depends(get_metrics),
):
    game = await repo.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    await repo.delete(game_id)
    metrics.increment("game.deleted")


@router.post("/{game_id}/coach", response_model=AICoachResponse)
async def coach_game(
    game_id: str,
    repo: GameRepository = Depends(get_game_repo),
    coach: AICoach = Depends(get_ai_coach),
    metrics: MetricsClient = Depends(get_metrics),
):
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

    recommended_x, recommended_y = recommended_position
    return AICoachResponse(
        game=GameResponse.model_validate(game),
        recommended_x=recommended_x,
        recommended_y=recommended_y,
        message=message,
    )
