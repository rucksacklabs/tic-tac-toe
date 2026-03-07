"""
Purpose: Core business logic for Tic-Tac-Toe game rules and moves.
Architecture: Domain Layer (Service).
Notes: Pure logic for board manipulation, win detection, and move processing.
"""

import json
import random
from typing import Protocol


class GameProtocol(Protocol):
    board: str
    status: str
    winner: str | None
    current_player: str


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


def create_board() -> list[str]:
    return [""] * 9


def apply_move(board: list[str], player: str, position: int) -> list[str]:
    if position < 0 or position > 8:
        raise GameError("Position out of range (0–8)")
    if player not in ("X", "O"):
        raise GameError("Player must be 'X' or 'O'")
    if board[position] != "":
        raise GameError("Cell is occupied")
    new_board = board.copy()
    new_board[position] = player
    return new_board


def check_winner(board: list[str]) -> str | None:
    for a, b, c in WINNING_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def check_draw(board: list[str]) -> bool:
    return all(cell != "" for cell in board) and check_winner(board) is None


def board_to_json(board: list[str]) -> str:
    return json.dumps(board)


def board_from_json(data: str) -> list[str]:
    return json.loads(data)


def make_new_game() -> dict:
    return {
        "board": board_to_json(create_board()),
        "current_player": "X",
        "status": "active",
        "winner": None,
    }


def process_move(game: GameProtocol, player: str, position: int) -> str | None:
    board = board_from_json(game.board)
    board = apply_move(board, player, position)

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
) -> tuple[str | None, list[tuple[str, int]]]:
    """Apply a human move and optional computer response, returning move trace."""

    board = board_from_json(game.board)
    human = game.current_player
    computer = "O" if human == "X" else "X"
    applied_moves: list[tuple[str, int]] = []

    # Human move
    board = apply_move(board, human, position)
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
    computer_position = random.choice(available)

    board = apply_move(board, computer, computer_position)
    applied_moves.append((computer, computer_position))

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


def play_turn_vs_computer(game: GameProtocol, position: int) -> str | None:
    """Apply a human move, then a random computer move if the game is still active.

    The human always plays as the current_player on the game object. The computer
    plays as the opposite marker and chooses a random available empty cell.
    """

    message, _ = play_turn_vs_computer_with_trace(game, position)
    return message
