"""
Purpose: REST API endpoints for game management and moves.
Architecture: Presentation Layer (API).
Notes: Handles request validation, routes to business logic services, and persists changes.
"""

import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.persistence.database import get_db
from app.models import Game, Move
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
from app.dependency_injection import get_ai_coach, get_metrics
from app.services.ai_coach import AICoach, AICoachError
from app.metrics.protocol import MetricsClient

router = APIRouter(prefix="/games", tags=["games"])


@router.post("", response_model=GameResponse, status_code=201)
async def create_game(
    db: AsyncSession = Depends(get_db),
    metrics: MetricsClient = Depends(get_metrics),
):
    game = Game(**make_new_game())
    db.add(game)
    await db.commit()
    await db.refresh(game)
    metrics.increment("game.created")
    return game


@router.get("/{game_id}", response_model=GameResponse)
async def get_game(game_id: str, db: AsyncSession = Depends(get_db)):
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game


@router.get("", response_model=list[GameResponse])
async def list_games(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Game).order_by(Game.created_at.asc(), Game.id.asc())
    )
    return list(result.scalars().all())


@router.post("/{game_id}/moves", response_model=MoveResponse)
async def make_move(
    game_id: str,
    move: MoveRequest,
    db: AsyncSession = Depends(get_db),
    metrics: MetricsClient = Depends(get_metrics),
):
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if game.status != "active":
        raise HTTPException(status_code=409, detail=f"Game is already {game.status}")

    # Map 0-based (x, y) coordinates to an internal 0–8 position index
    position = move.y * 3 + move.x

    try:
        message, applied_moves = play_turn_vs_computer_with_trace(game, position)
    except GameError as e:
        raise HTTPException(status_code=422, detail=str(e))

    current_max_move_number = await db.scalar(
        select(func.coalesce(func.max(Move.move_number), 0)).where(
            Move.game_id == game_id
        )
    )
    next_move_number = int(current_max_move_number or 0) + 1

    for player, move_position in applied_moves:
        db.add(
            Move(
                game_id=game_id,
                move_number=next_move_number,
                player=player,
                position=move_position,
            )
        )
        next_move_number += 1

    await db.commit()
    await db.refresh(game)

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
async def list_game_moves(game_id: str, db: AsyncSession = Depends(get_db)):
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    result = await db.execute(
        select(Move)
        .where(Move.game_id == game_id)
        .order_by(Move.move_number.asc(), Move.created_at.asc(), Move.id.asc())
    )
    return list(result.scalars().all())


@router.delete("/{game_id}", status_code=204)
async def delete_game(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    metrics: MetricsClient = Depends(get_metrics),
):
    game = await db.get(Game, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    await db.delete(game)
    await db.commit()
    metrics.increment("game.deleted")


@router.post("/{game_id}/coach", response_model=AICoachResponse)
async def coach_game(
    game_id: str,
    db: AsyncSession = Depends(get_db),
    coach: AICoach = Depends(get_ai_coach),
    metrics: MetricsClient = Depends(get_metrics),
):
    game = await db.get(Game, game_id)
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

    return AICoachResponse(
        game=GameResponse.model_validate(game),
        recommended_position=recommended_position,
        message=message,
    )
