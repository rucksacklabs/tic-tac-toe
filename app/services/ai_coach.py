"""
Purpose: Business logic for providing AI-based coaching advice.
Architecture: Domain Layer (Service).
Notes: Integrates with Anthropic API to recommend the best next move.
       Uses messages.parse with a Pydantic schema for structured output,
       so the SDK validates the response shape instead of manual JSON parsing.
"""

import json
from typing import Any

from anthropic import APIError, AsyncAnthropic
from pydantic import BaseModel, Field

from app.models import Game
from app.environment import Environment
from app.services.game_service import board_from_json


DEFAULT_MODEL = "claude-haiku-4-5"


class AICoachError(RuntimeError):
    pass


class CoachRecommendation(BaseModel):
    recommended_position: int = Field(ge=0, le=8)
    message: str


def _build_board_context(board: list[str]) -> dict[str, Any]:
    moves_played = sum(1 for cell in board if cell != "")
    available_positions = [i for i, cell in enumerate(board) if cell == ""]
    return {
        "board": board,
        "moves_played": moves_played,
        "available_positions": available_positions,
    }


def _build_system_prompt() -> str:
    return (
        "You are an AI coach for a simple tic-tac-toe game. "
        "You help a human choose the best next move on a 3x3 board."
    )


def _build_messages(game: Game) -> list[dict[str, str]]:
    board = board_from_json(game.board)
    context = _build_board_context(board)

    user_payload = {
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
        f"Game state JSON:\n{json.dumps(user_payload)}"
    )

    return [
        {"role": "user", "content": user},
    ]


class AICoach:
    def __init__(self, client: AsyncAnthropic):
        self.client = client

    async def get_ai_coach_recommendation(self, game: Game) -> tuple[int, str]:
        model = Environment.AI_COACH_MODEL_ENV or DEFAULT_MODEL
        board = board_from_json(game.board)
        available_positions = _build_board_context(board)["available_positions"]
        messages = _build_messages(game)

        try:
            response = await self.client.messages.parse(
                model=model,
                max_tokens=1024,
                system=_build_system_prompt(),
                messages=messages,
                temperature=0.2,
                output_format=CoachRecommendation,
            )
        except APIError as exc:
            raise AICoachError("Failed to contact AI coach provider") from exc
        except Exception as exc:  # pragma: no cover - safety net
            raise AICoachError("Unexpected error from AI coach provider") from exc

        # Edge case: stop_reason="max_tokens" means the response was cut off before the
        # schema could be satisfied. parsed_output may be None or incomplete. Increase
        # max_tokens if this is hit in production (current budget: 1024).
        if response.stop_reason == "max_tokens":
            raise AICoachError("AI coach response was truncated; increase max_tokens")

        # Edge case: stop_reason="refusal" means the model declined for safety reasons.
        # parsed_output will be None. Surface as a provider error so callers can retry
        # or surface a user-friendly message.
        if response.stop_reason == "refusal" or response.parsed_output is None:
            raise AICoachError("AI coach refused to provide a recommendation")

        position = response.parsed_output.recommended_position
        message = response.parsed_output.message

        if position not in available_positions:
            raise AICoachError(
                f"AI recommended position {position} is already occupied"
            )

        return position, message
