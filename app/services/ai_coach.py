"""
Purpose: Business logic for providing AI-based coaching advice.
Architecture: Domain Layer (Service).
Notes: Integrates with OpenAI API to recommend the best next move.
       Uses beta.chat.completions.parse with a Pydantic schema for structured output,
       so the SDK validates the response shape instead of manual JSON parsing.
"""

from dataclasses import dataclass
import dataclasses

import json
from typing import Any

from openai import APIError, AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field

from app.models import Board, Game
from app.environment import Environment
from app.services.game_service import board_from_json


DEFAULT_MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = (
    "You are an AI coach for a simple tic-tac-toe game. "
    "You help a human choose the best next move on a 3x3 board."
)


class AICoachError(RuntimeError):
    pass


class CoachRecommendation(BaseModel):
    recommended_position: int = Field(ge=0, le=8)
    message: str


def _build_board_context(board: Board) -> dict[str, Any]:
    moves_played = sum(1 for cell in board if cell != "")
    available_positions = [
        {"position": i} for i, cell in enumerate(board) if cell == ""
    ]
    return {
        "board": board,
        "moves_played": moves_played,
        "available_positions": available_positions,
    }


def _build_messages(game: Game) -> list[ChatCompletionMessageParam]:
    board = board_from_json(game.board)
    context = _build_board_context(board)

    game_state = {
        "board": context["board"],
        "moves_played": context["moves_played"],
        "available_positions": context["available_positions"],
        "current_player": game.current_player,
        "status": game.status,
        "winner": game.winner,
    }

    user = (
        "Given the current tic-tac-toe game state, recommend the best next move "
        "for the `current_player`.\n\n"
        f"Game state JSON:\n{json.dumps(game_state)}"
    )

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


@dataclass
class CoachStatus:
    ready: bool
    message: str


class AICoach:
    def __init__(self, client: AsyncOpenAI):
        self.client = client
        self.model = Environment.AI_COACH_MODEL_ENV or DEFAULT_MODEL

    async def get_ai_coach_recommendation(self, game: Game) -> tuple[int, str]:
        board = board_from_json(game.board)
        available_positions = _build_board_context(board)["available_positions"]
        messages = _build_messages(game)

        try:
            response = await self.client.beta.chat.completions.parse(
                model=self.model,
                max_tokens=1024,
                messages=messages,
                temperature=0.2,
                response_format=CoachRecommendation,
            )
        except APIError as exc:
            raise AICoachError("Failed to contact AI coach provider") from exc
        except Exception as exc:  # pragma: no cover - safety net
            raise AICoachError("Unexpected error from AI coach provider") from exc

        # Edge case: finish_reason="length" means the response was cut off before the
        # schema could be satisfied. Increase max_tokens if this is hit in production.
        choice = response.choices[0]
        if choice.finish_reason == "length":
            raise AICoachError("AI coach response was truncated; increase max_tokens")

        # Edge case: finish_reason="content_filter" means the model declined for safety.
        # parsed will be None. Surface as a provider error so callers can retry
        # or surface a user-friendly message.
        if choice.finish_reason == "content_filter" or choice.message.parsed is None:
            raise AICoachError("AI coach refused to provide a recommendation")

        rec_pos = choice.message.parsed.recommended_position
        message = choice.message.parsed.message

        if {"position": rec_pos} not in available_positions:
            raise AICoachError(f"AI recommended position {rec_pos} is already occupied")

        return rec_pos, message

    async def status(self) -> CoachStatus:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10,
            )

            if resp.choices:
                return CoachStatus(ready=True, message="AI coach is ready")
            else:
                return CoachStatus(ready=False, message="AI coach is not ready")
        except Exception as e:
            return CoachStatus(ready=False, message=f"AI coach is not ready: {e}")
