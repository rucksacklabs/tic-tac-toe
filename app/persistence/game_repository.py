# app/persistence/game_repository.py
"""
Purpose: Abstract interface for game persistence operations.
Architecture: Persistence Layer (Port).
Notes: Implementations include SqlAlchemyGameRepository (production)
       and InMemoryGameRepository (testing).
"""

from typing import Any, Protocol

from app.models import Game, Move


class GameRepository(Protocol):
    async def get(self, game_id: str) -> Game | None:
        """Fetch a game by ID. Returns None if not found."""
        ...

    async def create(self, game_data: dict[str, Any]) -> Game:
        """Create and persist a new game from an attribute dict."""
        ...

    async def save(self, game: Game) -> Game:
        """Persist pending changes to a game. Returns the updated game."""
        ...

    async def list_all(self) -> list[Game]:
        """Return all games ordered by creation time."""
        ...

    async def delete(self, game_id: str) -> None:
        """Delete a game and its associated moves."""
        ...

    async def add_moves(self, game_id: str, moves: list[dict[str, Any]]) -> None:
        """Append move records to a game.

        Each dict must contain keys: player, move_number, position.
        """
        ...

    async def get_moves(self, game_id: str) -> list[Move]:
        """Return moves for a game, ordered by move number."""
        ...

    async def count_moves(self, game_id: str) -> int:
        """Return the number of moves recorded for a game."""
        ...
