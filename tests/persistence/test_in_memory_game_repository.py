# tests/persistence/test_in_memory_game_repository.py
"""
Purpose: Unit tests for InMemoryGameRepository.
Architecture: Testing Layer (Unit).
Notes: Verifies the in-memory test double satisfies the GameRepository contract.
       No database infrastructure required.
"""

import pytest
from app.persistence.in_memory_game_repository import InMemoryGameRepository


def _new_game_data():
    return {
        "board": '["","","","","","","","",""]',
        "current_player": "X",
        "status": "active",
        "winner": None,
    }


@pytest.fixture
def repo():
    return InMemoryGameRepository()


async def test_create_returns_game_with_id(repo):
    game = await repo.create(_new_game_data())
    assert game.id is not None
    assert game.status == "active"


async def test_get_returns_created_game(repo):
    created = await repo.create(_new_game_data())
    fetched = await repo.get(created.id)
    assert fetched is not None
    assert fetched.id == created.id


async def test_get_returns_none_for_missing_id(repo):
    assert await repo.get("nonexistent") is None


async def test_list_all_returns_all_games(repo):
    await repo.create(_new_game_data())
    await repo.create(_new_game_data())
    games = await repo.list_all()
    assert len(games) == 2


async def test_save_persists_mutations(repo):
    game = await repo.create(_new_game_data())
    game.status = "won"
    game.winner = "X"
    await repo.save(game)
    fetched = await repo.get(game.id)
    assert fetched.status == "won"
    assert fetched.winner == "X"


async def test_delete_removes_game(repo):
    game = await repo.create(_new_game_data())
    await repo.delete(game.id)
    assert await repo.get(game.id) is None


async def test_add_moves_and_get_moves(repo):
    game = await repo.create(_new_game_data())
    await repo.add_moves(
        game.id,
        [
            {"player": "X", "move_number": 1, "x": 0, "y": 0},
            {"player": "O", "move_number": 2, "x": 1, "y": 1},
        ],
    )
    moves = await repo.get_moves(game.id)
    assert len(moves) == 2
    assert moves[0].player == "X"
    assert moves[1].player == "O"


async def test_count_moves(repo):
    game = await repo.create(_new_game_data())
    assert await repo.count_moves(game.id) == 0
    await repo.add_moves(
        game.id,
        [
            {"player": "X", "move_number": 1, "x": 0, "y": 0},
        ],
    )
    assert await repo.count_moves(game.id) == 1


async def test_get_moves_returns_ordered_by_move_number(repo):
    game = await repo.create(_new_game_data())
    await repo.add_moves(
        game.id,
        [
            {"player": "O", "move_number": 2, "x": 1, "y": 1},
            {"player": "X", "move_number": 1, "x": 0, "y": 0},
        ],
    )
    moves = await repo.get_moves(game.id)
    assert [m.move_number for m in moves] == [1, 2]


async def test_delete_also_removes_moves(repo):
    game = await repo.create(_new_game_data())
    await repo.add_moves(
        game.id,
        [
            {"player": "X", "move_number": 1, "x": 0, "y": 0},
        ],
    )
    await repo.delete(game.id)
    assert await repo.get_moves(game.id) == []
