"""
Purpose: Core business logic for Tic-Tac-Toe game rules and moves.
Architecture: Domain Layer (Service).
Notes: Pure logic for board manipulation, win detection, and move processing.
       Internally uses flat position index (0–8). Translation to/from x/y coordinates
       happens exclusively at the API layer.
"""

import json
import random
from typing import Protocol, cast

from app.models import Board, Cell, Player, GameStatus, MoveTrace


class GameProtocol(Protocol):
    board: str
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
    return cast(Board, [""] * 9)


def apply_move(*, board: Board, player: Player, position: int) -> Board:
    if not (0 <= position <= 8):
        raise GameError("Position out of range (must be 0–8)")
    if player not in ("X", "O"):
        raise GameError("Player must be 'X' or 'O'")
    if board[position] != "":
        raise GameError("Cell is occupied")
    new_board = list(board)
    new_board[position] = player
    return new_board


def check_winner(board: Board) -> Player | None:
    for a, b, c in WINNING_LINES:
        cell = board[a]
        if cell and cell == board[b] == board[c]:
            return cell
    return None


def check_draw(board: Board) -> bool:
    return all(cell != "" for cell in board) and check_winner(board) is None


def board_to_json(board: Board) -> str:
    return json.dumps(board)


def board_from_json(data: str) -> Board:
    return json.loads(data)


def make_new_game() -> dict:
    return {
        "board": board_to_json(new_board()),
        "current_player": "X",
        "status": "active",
        "winner": None,
    }


def process_move(game: GameProtocol, player: Player, position: int) -> str | None:
    board = board_from_json(game.board)
    board = apply_move(board=board, player=player, position=position)

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
    game: GameProtocol, position: int
) -> tuple[str | None, MoveTrace]:
    """Apply a human move and optional computer response, returning move trace.

    Returns a tuple of (message, applied_moves) where each applied move is a
    (player, position) tuple using flat index (0–8).
    """

    board = board_from_json(game.board)
    human = game.current_player
    computer = "O" if human == "X" else "X"
    applied_moves: MoveTrace = []

    # Human move
    board = apply_move(board=board, player=human, position=position)
    applied_moves.append((human, position))

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
    available = [i for i, cell in enumerate(board) if cell == ""]
    computer_pos = random.choice(available)

    board = apply_move(board=board, player=computer, position=computer_pos)
    applied_moves.append((computer, computer_pos))

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
