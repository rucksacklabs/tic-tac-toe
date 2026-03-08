"""
Purpose: Core business logic for Tic-Tac-Toe game rules and moves.
Architecture: Domain Layer (Service).
Notes: Pure logic for board manipulation, win detection, and move processing.
       Coordinates are 0-based (x, y) where (0, 0) is top-left and (2, 2) is bottom-right.
"""

import json
import random
from typing import Protocol

from app.models import Board, Player, GameStatus, MoveTrace


class GameProtocol(Protocol):
    board: Board
    status: GameStatus
    winner: Player | None
    current_player: Player


WINNING_LINES = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),  # rows
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),  # columns
    (0, 4, 8),
    (2, 4, 6),  # diagonals
]


class GameError(ValueError):
    pass


def new_board() -> Board:
    return Board([None] * 9)


def _pos(x: int, y: int) -> int:
    """Convert (x, y) coordinates to a flat board index."""
    return y * 3 + x


def apply_move(*, board: Board, player: Player, x: int, y: int) -> Board:
    if not (0 <= x <= 2 and 0 <= y <= 2):
        raise GameError("Position out of range (x and y must be 0–2)")
    if player not in ("X", "O"):
        raise GameError("Player must be 'X' or 'O'")
    position = _pos(x, y)
    if board[position] != "":
        raise GameError("Cell is occupied")
    new_board = list(board)
    new_board[position] = player
    return new_board


def check_winner(board: Board) -> Player | None:
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def check_draw(board: Board) -> bool:
    return all(cell != "" for cell in board) and check_winner(board) is None


def board_to_json(board: Board) -> str:
    return json.dumps(board)


def board_from_json(data: str) -> Board:
    return Board(json.loads(data))


def make_new_game() -> dict:
    return {
        "board": board_to_json(new_board()),
        "current_player": "X",
        "status": "active",
        "winner": None,
    }


def process_move(game: GameProtocol, player: Player, x: int, y: int) -> str | None:
    board = board_from_json(game.board)
    board = apply_move(board=board, player=player, x=x, y=y)

    winner = check_winner(board)
    if winner:
        game.status = "won"
        game.winner = winner
        game.board = board_to_json(board)
        return f"Player {winner} wins!"

    if check_draw(board):
        game.status = "draw"
        game.board = board_to_json(board)
        return "It's a draw!"

    game.current_player = "O" if player == "X" else "X"
    game.board = board_to_json(board)
    return None


def play_turn_vs_computer_with_trace(
    game: GameProtocol, x: int, y: int
) -> tuple[str | None, MoveTrace]:
    """Apply a human move and optional computer response, returning move trace.

    Returns a tuple of (message, applied_moves) where each applied move is a
    (player, x, y) tuple using 0-based coordinates.
    """

    board = board_from_json(game.board)
    human = game.current_player
    computer = "O" if human == "X" else "X"
    applied_moves: MoveTrace = []

    # Human move
    board = apply_move(board=board, player=human, x=x, y=y)
    applied_moves.append((human, x, y))

    winner = check_winner(board)
    if winner:
        game.status = "won"
        game.winner = winner
        game.board = board_to_json(board)
        return f"Player {winner} wins!", applied_moves

    if check_draw(board):
        game.status = "draw"
        game.board = board_to_json(board)
        return "It's a draw!", applied_moves

    # Computer move (random available empty cell)
    available = [(i % 3, i // 3) for i, cell in enumerate(board) if cell == ""]
    computer_x, computer_y = random.choice(available)

    board = apply_move(board=board, player=computer, x=computer_x, y=computer_y)
    applied_moves.append((computer, computer_x, computer_y))

    winner = check_winner(board)
    if winner:
        game.status = "won"
        game.winner = winner
        game.board = board_to_json(board)
        return f"Player {winner} wins!", applied_moves

    if check_draw(board):
        game.status = "draw"
        game.board = board_to_json(board)
        return "It's a draw!", applied_moves

    game.board = board_to_json(board)
    return None, applied_moves
