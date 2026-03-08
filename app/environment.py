"""
Purpose: Centralized management of environment variables and application configuration.
Architecture: Configuration Layer.
Notes: Provides a structured way to access configuration values with defaults.
"""

import os
from typing import Any, Type, cast


class Environment:
    OPENAI_API_KEY_ENV = os.getenv("OPENAI_API_KEY")
    AI_COACH_MODEL_ENV = os.getenv("AI_COACH_MODEL") or "gpt-4o-mini"
    DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./tic_tac_toe.db"
