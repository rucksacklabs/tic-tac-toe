"""
Purpose: Unit tests for the Game service (core logic).
Architecture: Testing Layer (Unit).
Notes: Verifies board manipulation, win/draw detection, and move rules.
"""

import pytest
from app.services.game_service import (
    create_board,
    apply_move,
    check_winner,
    check_draw,
    board_to_json,
    play_turn_vs_computer_with_trace,
    GameError,
)


def test_create_board_returns_9_empty_cells():
    board = create_board()
    assert board == [""] * 9


def test_apply_move_places_player():
    board = [""] * 9
    result = apply_move(board, "X", 0)
    assert result[0] == "X"


def test_apply_move_raises_on_occupied_cell():
    board = ["X"] + [""] * 8
    with pytest.raises(GameError, match="occupied"):
        apply_move(board, "O", 0)


def test_apply_move_raises_on_out_of_bounds():
    board = [""] * 9
    with pytest.raises(GameError, match="out of range"):
        apply_move(board, "X", 9)


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
    board = [""] * 9
    assert check_winner(board) is None


def test_check_draw_true_when_full_no_winner():
    board = ["X", "O", "X", "X", "O", "X", "O", "X", "O"]
    assert check_draw(board) is True


def test_check_draw_false_when_not_full():
    board = ["X", "O", "", "", "", "", "", "", ""]
    assert check_draw(board) is False


def test_apply_move_raises_on_invalid_player():
    board = [""] * 9
    with pytest.raises(GameError, match="Player must be"):
        apply_move(board, "Z", 0)


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
