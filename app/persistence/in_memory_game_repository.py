# app/persistence/in_memory_game_repository.py
"""
Purpose: In-memory implementation of GameRepository for testing.
Architecture: Persistence Layer (Test Double).
Notes: Stores games and moves in plain dicts. No database required.
"""

import uuid
from datetime import datetime, timezone

from app.models import Game, Move


class InMemoryGameRepository:
    def __init__(self):
        self._games: dict[str, Game] = {}
        self._moves: dict[str, list[Move]] = {}

    async def get(self, game_id: str) -> Game | None:
        return self._games.get(game_id)

    async def create(self, game_data: dict) -> Game:
        game = Game(**game_data)
        if not game.id:
            game.id = str(uuid.uuid4())
        if not game.created_at:
            game.created_at = datetime.now(timezone.utc)
        self._games[game.id] = game
        self._moves[game.id] = []
        return game

    async def save(self, game: Game) -> Game:
        self._games[game.id] = game
        return game

    async def list_all(self) -> list[Game]:
        return sorted(self._games.values(), key=lambda g: g.created_at)

    async def delete(self, game_id: str) -> None:
        self._games.pop(game_id, None)
        self._moves.pop(game_id, None)

    async def add_moves(self, game_id: str, moves: list[dict]) -> None:
        if game_id not in self._moves:
            self._moves[game_id] = []
        for move_data in moves:
            move = Move(
                id=str(uuid.uuid4()),
                game_id=game_id,
                created_at=datetime.now(timezone.utc),
                **move_data,
            )
            self._moves[game_id].append(move)

    async def get_moves(self, game_id: str) -> list[Move]:
        moves = self._moves.get(game_id, [])
        return sorted(moves, key=lambda m: m.move_number)

    async def count_moves(self, game_id: str) -> int:
        return len(self._moves.get(game_id, []))
