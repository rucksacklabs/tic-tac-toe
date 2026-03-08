"""
Purpose: Integration tests for the Games API endpoints.
Architecture: Testing Layer (Integration).
Notes: Uses an in-memory SQLite database and test client to verify API behavior.
"""

from datetime import datetime
from unittest.mock import patch

import pytest
from httpx import AsyncClient, ASGITransport

from app.persistence.in_memory_game_repository import InMemoryGameRepository
from app.dependency_injection import get_game_repo
from main import app


@pytest.fixture
def repo():
    return InMemoryGameRepository()


@pytest.fixture
async def client(repo):
    app.dependency_overrides[get_game_repo] = lambda: repo
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.pop(get_game_repo, None)


async def test_create_game(client):
    response = await client.post("/games")
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "active"
    assert data["current_player"] == "X"
    assert data["board"] == [""] * 9


async def test_get_game(client):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]
    response = await client.get(f"/games/{game_id}")
    assert response.status_code == 200
    assert response.json()["id"] == game_id


async def test_get_game_not_found(client):
    response = await client.get("/games/nonexistent-id")
    assert response.status_code == 404


async def test_list_games_returns_chronological_order(client):
    await client.post("/games")
    await client.post("/games")

    response = await client.get("/games")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    created_at_values = [datetime.fromisoformat(item["created_at"]) for item in data]
    assert created_at_values == sorted(created_at_values)


async def test_make_valid_move(client):
    game_id = (await client.post("/games")).json()["id"]
    response = await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert response.status_code == 200
    data = response.json()
    # Human plays as X at (0, 0); computer replies as O in the next free cell.
    assert data["board"][0] == "X"
    assert "O" in data["board"]
    assert data["status"] == "active"


async def test_make_move_on_finished_game(client):
    # Create and immediately finish a game, then ensure further moves are rejected.
    # Patch random.choice so O never blocks X's main diagonal (0,0)→(1,1)→(2,2).
    game_id = (await client.post("/games")).json()["id"]
    with patch(
        "app.services.game_service.random.choice", side_effect=lambda seq: seq[0]
    ):
        # X at (0, 0), O picks first available
        await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
        # X at (1, 1), O picks first available
        await client.post(f"/games/{game_id}/moves", json={"x": 1, "y": 1})
        # X at (2, 2) → Player X wins (diagonal)
        await client.post(f"/games/{game_id}/moves", json={"x": 2, "y": 2})

    response = await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 2})
    assert response.status_code == 409


async def test_make_move_occupied_cell(client):
    game_id = (await client.post("/games")).json()["id"]
    await client.post(f"/games/{game_id}/moves", json={"x": 1, "y": 1})
    response = await client.post(f"/games/{game_id}/moves", json={"x": 1, "y": 1})
    assert response.status_code == 422


async def test_make_move_out_of_bounds(client):
    game_id = (await client.post("/games")).json()["id"]
    response = await client.post(f"/games/{game_id}/moves", json={"x": 3, "y": 0})
    assert response.status_code == 422


async def test_win_detection(client):
    game_id = (await client.post("/games")).json()["id"]
    # TODO: review — patching random.choice to make O deterministic is a smell.
    # Consider exposing a computer_strategy seam on the game service instead,
    # or testing win detection at the service layer where board state can be set directly.
    # X takes the main diagonal: (0,0) → (1,1) → (2,2).
    # Patch random.choice so O picks first available and never blocks X's path.
    with patch(
        "app.services.game_service.random.choice", side_effect=lambda seq: seq[0]
    ):
        await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
        await client.post(f"/games/{game_id}/moves", json={"x": 1, "y": 1})
        last_resp = await client.post(f"/games/{game_id}/moves", json={"x": 2, "y": 2})

    data = last_resp.json()
    assert data["status"] == "won"
    assert data["winner"] == "X"
    assert "wins" in data["message"]


async def test_draw_detection(client):
    game_id = (await client.post("/games")).json()["id"]
    # TODO: review — patching random.choice to make O deterministic is a smell.
    # Consider exposing a computer_strategy seam on the game service instead,
    # or testing draw detection at the service layer where board state can be set directly.
    # Play moves that lead to a draw. The specific sequence relies on O always
    # picking the first available cell, so random.choice is patched here.
    #
    # X plays positions (1, 3, 4, 6, 8), O fills (0, 2, 5, 7) in order:
    #   1. X at (1, 0) → pos 1, O → pos 0
    #   2. X at (0, 1) → pos 3, O → pos 2
    #   3. X at (1, 1) → pos 4, O → pos 5
    #   4. X at (0, 2) → pos 6, O → pos 7
    #   5. X at (2, 2) → pos 8, draw
    human_moves = [
        {"x": 1, "y": 0},
        {"x": 0, "y": 1},
        {"x": 1, "y": 1},
        {"x": 0, "y": 2},
        {"x": 2, "y": 2},
    ]

    last_resp = None
    with patch(
        "app.services.game_service.random.choice", side_effect=lambda seq: seq[0]
    ):
        for move in human_moves:
            last_resp = await client.post(
                f"/games/{game_id}/moves",
                json=move,
            )

    assert last_resp is not None
    assert last_resp.json()["status"] == "draw"


async def test_list_game_moves_returns_chronological_history(client):
    game_id = (await client.post("/games")).json()["id"]
    move_response = await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert move_response.status_code == 200

    response = await client.get(f"/games/{game_id}/moves")
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert [move["move_number"] for move in data] == [1, 2]
    assert [move["player"] for move in data] == ["X", "O"]
    assert data[0]["x"] == 0 and data[0]["y"] == 0
    assert (
        0 <= data[1]["x"] <= 2 and 0 <= data[1]["y"] <= 2
    )  # computer picks a random available cell


async def test_list_game_moves_not_found(client):
    response = await client.get("/games/nonexistent-id/moves")
    assert response.status_code == 404


async def test_delete_game(client):
    game_id = (await client.post("/games")).json()["id"]
    response = await client.delete(f"/games/{game_id}")
    assert response.status_code == 204
    get_resp = await client.get(f"/games/{game_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_ai_coach_endpoint_happy_path(client):
    from unittest.mock import AsyncMock
    from app.dependency_injection import get_ai_coach

    game_id = (await client.post("/games")).json()["id"]

    mock_coach = AsyncMock()
    mock_coach.get_ai_coach_recommendation = AsyncMock(
        return_value=((1, 1), "Play in the center.")
    )

    app.dependency_overrides[get_ai_coach] = lambda: mock_coach
    try:
        response = await client.post(f"/games/{game_id}/coach")
    finally:
        app.dependency_overrides.pop(get_ai_coach, None)

    assert response.status_code == 200
    data = response.json()
    assert data["recommended_x"] == 1 and data["recommended_y"] == 1
    assert "center" in data["message"]
    assert data["game"]["id"] == game_id


@pytest.mark.asyncio
async def test_ai_coach_endpoint_game_not_found(client):
    from unittest.mock import AsyncMock
    from app.dependency_injection import get_ai_coach

    app.dependency_overrides[get_ai_coach] = lambda: AsyncMock()
    try:
        response = await client.post("/games/nonexistent-id/coach")
    finally:
        app.dependency_overrides.pop(get_ai_coach, None)

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ai_coach_endpoint_conflict_on_finished_game(client):
    from unittest.mock import AsyncMock
    from app.dependency_injection import get_ai_coach

    game_id = (await client.post("/games")).json()["id"]
    # TODO: review — patching random.choice to make O deterministic is a smell.
    # Consider setting game status directly in the DB fixture instead of playing
    # moves through the API, which would remove the dependency on computer strategy entirely.
    # Force game to a non-active status via normal moves (diagonal win for X).
    # Patch random.choice so O never blocks X's diagonal.
    with patch(
        "app.services.game_service.random.choice", side_effect=lambda seq: seq[0]
    ):
        await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
        await client.post(f"/games/{game_id}/moves", json={"x": 1, "y": 1})
        await client.post(f"/games/{game_id}/moves", json={"x": 2, "y": 2})

    # The coach endpoint should short-circuit with 409 before calling the AI provider.
    app.dependency_overrides[get_ai_coach] = lambda: AsyncMock()
    try:
        response = await client.post(f"/games/{game_id}/coach")
    finally:
        app.dependency_overrides.pop(get_ai_coach, None)

    assert response.status_code == 409
