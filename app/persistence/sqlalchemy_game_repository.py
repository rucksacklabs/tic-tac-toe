# app/persistence/sqlalchemy_game_repository.py
"""
Purpose: SQLAlchemy implementation of GameRepository.
Architecture: Persistence Layer (Adapter).
Notes: This is the only module that depends on AsyncSession.
       All SQLAlchemy query and transaction logic lives here.
"""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Game, Move


class SqlAlchemyGameRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, game_id: str) -> Game | None:
        return await self._session.get(Game, game_id)

    async def create(self, game_data: dict[str, Any]) -> Game:
        game = Game(**game_data)
        self._session.add(game)
        await self._session.commit()
        await self._session.refresh(game)
        return game

    async def save(self, game: Game) -> Game:
        await self._session.commit()
        await self._session.refresh(game)
        return game

    async def list_all(self) -> list[Game]:
        result = await self._session.execute(
            select(Game).order_by(Game.created_at.asc(), Game.id.asc())
        )
        return list(result.scalars().all())

    async def delete(self, game_id: str) -> None:
        game = await self._session.get(Game, game_id)
        if game:
            await self._session.delete(game)
            await self._session.commit()

    async def add_moves(self, game_id: str, moves: list[dict[str, Any]]) -> None:
        for move_data in moves:
            self._session.add(Move(game_id=game_id, **move_data))
        await self._session.commit()

    async def get_moves(self, game_id: str) -> list[Move]:
        result = await self._session.execute(
            select(Move)
            .where(Move.game_id == game_id)
            .order_by(Move.move_number.asc(), Move.created_at.asc(), Move.id.asc())
        )
        return list(result.scalars().all())

    async def count_moves(self, game_id: str) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(Move).where(Move.game_id == game_id)
        )
        return result.scalar() or 0
