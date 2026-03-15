"""
Purpose: Unit tests for the AI Coach service.
Architecture: Testing Layer (Unit).
Notes: Mocks the OpenAI client to test recommendation logic.
       beta.chat.completions.parse handles schema validation so no manual JSON parsing tests needed.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.ai_coach import (
    AICoach,
    AICoachError,
    CoachRecommendation,
    _build_board_context,
)
from app.models import Board, Game


def make_game(board: Board | None = None) -> Game:
    game = Game()
    game.board = json.dumps(board or [""] * 9)
    game.current_player = "X"
    game.status = "active"
    game.winner = None
    return game


def make_parse_response(
    position: int, message: str, finish_reason: str = "stop"
) -> MagicMock:
    rec = CoachRecommendation(recommended_position=position, message=message)
    choice = MagicMock()
    choice.finish_reason = finish_reason
    choice.message.parsed = rec
    response = MagicMock()
    response.choices = [choice]
    return response


def test_build_board_context_basic():
    board: Board = ["X", "O", "", "", "", "", "", "", ""]
    ctx = _build_board_context(board)
    assert ctx["moves_played"] == 2
    assert ctx["available_positions"] == [{"position": i} for i in range(2, 9)]


@pytest.mark.asyncio
async def test_get_ai_coach_recommendation_uses_client_and_parses_result():
    game = make_game()

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse.return_value = make_parse_response(
        0, "Take the first free cell."
    )

    coach = AICoach(mock_client)
    pos, msg = await coach.get_ai_coach_recommendation(game)

    assert pos == 0
    assert "first free cell" in msg
    mock_client.beta.chat.completions.parse.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_ai_coach_recommendation_raises_on_occupied_position():
    # Board with X at position 0 — AI recommends position 0 which is occupied
    game = make_game(board=["X", "", "", "", "", "", "", "", ""])

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse.return_value = make_parse_response(
        0, "Take position 0."
    )

    coach = AICoach(mock_client)
    with pytest.raises(AICoachError, match="already occupied"):
        await coach.get_ai_coach_recommendation(game)


@pytest.mark.asyncio
async def test_get_ai_coach_recommendation_raises_on_refusal():
    game = make_game()

    choice = MagicMock()
    choice.finish_reason = "content_filter"
    choice.message.parsed = None
    response = MagicMock()
    response.choices = [choice]

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse.return_value = response

    coach = AICoach(mock_client)
    with pytest.raises(AICoachError, match="refused"):
        await coach.get_ai_coach_recommendation(game)


@pytest.mark.asyncio
async def test_get_ai_coach_recommendation_raises_on_max_tokens():
    game = make_game()

    choice = MagicMock()
    choice.finish_reason = "length"
    choice.message.parsed = None
    response = MagicMock()
    response.choices = [choice]

    mock_client = AsyncMock()
    mock_client.beta.chat.completions.parse.return_value = response

    coach = AICoach(mock_client)
    with pytest.raises(AICoachError, match="truncated"):
        await coach.get_ai_coach_recommendation(game)
