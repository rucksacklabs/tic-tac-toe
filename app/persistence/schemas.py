"""
Purpose: Pydantic schemas for data validation and serialization.
Architecture: Application Layer (Data Transfer Objects).
Notes: Used for validating API requests and serializing API responses.
"""

import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_serializer, field_validator

from app.models import GameStatus, Player


Cell = Literal["", "X", "O"]


class Board(BaseModel):
    """Tic-tac-toe board: 9 cells, each "" or "X" or "O"."""

    cells: list[Cell]

    @field_validator("cells")
    @classmethod
    def check_length(cls, v: list) -> list[Cell]:
        if len(v) != 9:
            raise ValueError("Board must have exactly 9 cells")
        return v

    @field_validator("cells", mode="before")
    @classmethod
    def parse_cells(cls, v: str | list) -> list:
        if isinstance(v, str):
            v = json.loads(v)
        return ["" if cell == "." else cell for cell in v]

    def to_list(self) -> list[Cell]:
        return list(self.cells)


class GameResponse(BaseModel):
    id: str
    board: Board
    current_player: Player
    status: GameStatus
    winner: Player | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}

    @field_validator("board", mode="before")
    @classmethod
    def parse_board(cls, v: str | list | dict) -> Board:
        if isinstance(v, Board):
            return v
        if isinstance(v, str):
            v = json.loads(v)
        if isinstance(v, list):
            return Board(cells=v)
        if isinstance(v, dict) and "cells" in v:
            return Board(**v)
        raise ValueError(f"Cannot parse board from {type(v).__name__}: {v!r}")

    @field_serializer("board")
    def serialize_board(self, board: Board) -> list:
        return ["." if cell == "" else cell for cell in board.to_list()]


class MoveRequest(BaseModel):
    """Request payload for making the next move.

    Coordinates are 0-based, where (0, 0) is the top-left corner and (2, 2) is
    the bottom-right corner of the 3×3 board.
    """

    x: int
    y: int

    @field_validator("x", "y")
    @classmethod
    def check_coordinate(cls, v: int) -> int:
        if not 0 <= v <= 2:
            raise ValueError("Coordinates must be between 0 and 2 (inclusive)")
        return v


class MoveResponse(GameResponse):
    message: str | None = None


class MoveHistoryItem(BaseModel):
    id: str
    game_id: str
    move_number: int
    player: Player
    x: int
    y: int
    created_at: datetime

    model_config = {"from_attributes": True}


class AICoachRequest(BaseModel):
    pass


class AICoachResponse(BaseModel):
    game: GameResponse
    recommended_x: int
    recommended_y: int
    message: str
