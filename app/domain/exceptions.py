# app/domain/exceptions.py
"""
Purpose: Domain-level exceptions for game operations.
Architecture: Domain Layer.
Notes: Used by the API layer to map business errors to HTTP responses.
"""


class GameNotFoundError(Exception):
    def __init__(self, game_id: str):
        self.game_id = game_id
        super().__init__(f"Game {game_id} not found")


class GameFinishedError(Exception):
    def __init__(self, game_id: str, status: str):
        self.game_id = game_id
        self.status = status
        super().__init__(f"Game {game_id} is already {status}")
