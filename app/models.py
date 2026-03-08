"""
Purpose: SQLAlchemy ORM models representing the database schema.
Architecture: Persistence Layer (Data Models).
Notes: Defines Game and Move tables with relationships.
"""

from typing import List, Literal
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.persistence.database import Base
from pydantic import RootModel

type Player = Literal["X", "O"]
type Cell = Literal["X", "O", ""]
type GameStatus = Literal["active", "won", "draw"]
type Board = List[Cell]
type MoveTrace = list[tuple[Player, int]]


class Game(Base):
    __tablename__ = "games"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    board: Mapped[str] = mapped_column(String, default='["","","","","","","","",""]')
    current_player: Mapped[Player] = mapped_column(String, default="X")
    status: Mapped[GameStatus] = mapped_column(
        String, default="active"
    )  # active | won | draw
    winner: Mapped[Player | None] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    moves: Mapped[list["Move"]] = relationship(
        back_populates="game", cascade="all, delete-orphan"
    )


class Move(Base):
    __tablename__ = "moves"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    game_id: Mapped[str] = mapped_column(ForeignKey("games.id"), index=True)
    move_number: Mapped[int] = mapped_column(Integer, nullable=False)
    player: Mapped[Player] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    game: Mapped[Game] = relationship(back_populates="moves")
