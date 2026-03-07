"""
Purpose: Centralized management of environment variables and application configuration.
Architecture: Configuration Layer.
Notes: Provides a structured way to access configuration values with defaults.
"""

import os
from typing import Any, Type, cast


class Environment:
    ANTHROPIC_API_KEY_ENV = os.getenv("ANTHROPIC_API_KEY")
    AI_COACH_MODEL_ENV = os.getenv("AI_COACH_MODEL") or "claude-opus-4-6"
    DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./tic_tac_toe.db"
