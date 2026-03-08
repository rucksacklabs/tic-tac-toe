# tests/persistence/test_sqlalchemy_game_repository.py
"""
Purpose: Integration tests for SqlAlchemyGameRepository.
Architecture: Testing Layer (Integration).
Notes: These tests verify SQLAlchemy operations against an in-memory database.
       This is the ONLY test file that requires database infrastructure.
"""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.persistence.database import Base
from app.persistence.sqlalchemy_game_repository import SqlAlchemyGameRepository


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


def _new_game_data():
    return {
        "board": '["","","","","","","","",""]',
        "current_player": "X",
        "status": "active",
        "winner": None,
    }


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def repo():
    async with TestSessionLocal() as session:
        yield SqlAlchemyGameRepository(session)


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
            {"player": "X", "move_number": 1, "position": 0},
            {"player": "O", "move_number": 2, "position": 4},
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
            {"player": "X", "move_number": 1, "position": 0},
        ],
    )
    assert await repo.count_moves(game.id) == 1


async def test_get_moves_returns_ordered_by_move_number(repo):
    game = await repo.create(_new_game_data())
    await repo.add_moves(
        game.id,
        [
            {"player": "O", "move_number": 2, "position": 4},
            {"player": "X", "move_number": 1, "position": 0},
        ],
    )
    moves = await repo.get_moves(game.id)
    assert [m.move_number for m in moves] == [1, 2]


async def test_delete_cascades_to_moves(repo):
    game = await repo.create(_new_game_data())
    await repo.add_moves(
        game.id,
        [
            {"player": "X", "move_number": 1, "position": 0},
        ],
    )
    await repo.delete(game.id)
    assert await repo.get(game.id) is None
    assert await repo.get_moves(game.id) == []
