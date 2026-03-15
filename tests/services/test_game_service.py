"""
Purpose: Unit tests for the Game service (core logic).
Architecture: Testing Layer (Unit).
Notes: Verifies board manipulation, win/draw detection, and move rules.
"""

import pytest
from app.models import Board

from app.services.game_service import (
    GameError,
    apply_move,
    board_to_json,
    check_draw,
    check_winner,
    new_board,
    play_turn_vs_computer_with_trace,
)


def test_create_board_returns_9_empty_cells():
    board = new_board()
    assert board == [""] * 9


def test_apply_move_places_player():
    board = new_board()
    result = apply_move(board=board, player="X", position=0)
    assert result[0] == "X"


def test_apply_move_raises_on_occupied_cell():
    board: Board = ["X"] + [""] * 8
    with pytest.raises(GameError, match="occupied"):
        apply_move(board=board, player="O", position=0)


def test_apply_move_raises_on_out_of_bounds():
    board = new_board()
    with pytest.raises(GameError, match="out of range"):
        apply_move(board=board, player="X", position=9)


def test_check_winner_detects_row():
    board = ["X", "X", "X", "", "", "", "", "", ""]
    assert check_winner(board) == "X"


def test_check_winner_detects_column():
    board = ["O", "", "", "O", "", "", "O", "", ""]
    assert check_winner(board) == "O"


def test_check_winner_detects_diagonal():
    board = ["X", "", "", "", "X", "", "", "", "X"]
    assert check_winner(board) == "X"


def test_check_winner_returns_none_when_no_winner():
    board = new_board()
    assert check_winner(board) is None


def test_check_draw_true_when_full_no_winner():
    board = ["X", "O", "X", "X", "O", "X", "O", "X", "O"]
    assert check_draw(board) is True


def test_check_draw_false_when_not_full():
    board = ["X", "O", "", "", "", "", "", "", ""]
    assert check_draw(board) is False


def test_apply_move_raises_on_invalid_player():
    board = new_board()
    with pytest.raises(GameError, match="Player must be"):
        apply_move(board=board, player="Z", position=0)


def test_computer_picks_random_available_cell():
    """Computer should not always pick the same cell when multiple are available."""

    class FakeGame:
        board = board_to_json(["X", "", "", "", "", "", "", "", ""])
        status = "active"
        winner = None
        current_player = "O"

    chosen_positions = set()
    for _ in range(20):
        game = FakeGame()
        _, moves = play_turn_vs_computer_with_trace(game, 1)
        computer_moves = [pos for player, pos in moves if player == "X"]
        if computer_moves:
            chosen_positions.add(computer_moves[0])

    assert len(chosen_positions) > 1, (
        "Computer always picked the same position — not random"
    )


def test_draw_on_human_final_move_has_no_computer_response():
    """Computer must not get a move when the human's move fills the board for a draw."""

    # Board: 8 cells filled, position 8 empty — playing it yields no winner → draw
    # Layout: X O X / X O X / O X _
    class FakeGame:
        board = board_to_json(["X", "O", "X", "X", "O", "X", "O", "X", ""])
        status = "active"
        winner = None
        current_player = "O"

    game = FakeGame()
    message, moves = play_turn_vs_computer_with_trace(game, 8)

    assert message == "It's a draw!"
    assert game.status == "draw"
    assert len(moves) == 1, "Computer should not move after human draws the game"
    assert moves[0] == ("O", 8)


def test_computer_is_forced_to_the_only_available_cell():
    """When only one cell remains after the human move, the computer must pick it."""

    # Board: 7 filled, positions 5 and 8 empty
    # Human (X) plays 5 → leaves only position 8 for computer (O)
    # Layout: X O X / X O _ / O X _
    class FakeGame:
        board = board_to_json(["X", "O", "X", "X", "O", "", "O", "X", ""])
        status = "active"
        winner = None
        current_player = "X"

    game = FakeGame()
    _, moves = play_turn_vs_computer_with_trace(game, 5)

    assert len(moves) == 2
    assert moves[0] == ("X", 5)
    assert moves[1] == ("O", 8), "Computer must pick the only available cell"
