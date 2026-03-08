# Tic-Tac-Toe API

A REST API for multi-session tic-tac-toe built with FastAPI, SQLAlchemy, and SQLite.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Run

```bash
uv run python main.py
```

API available at http://localhost:8000
Interactive docs at http://localhost:8000/docs

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/games` | Create a new game |
| GET | `/games` | List all games in chronological order |
| GET | `/games/{id}` | Get game state |
| POST | `/games/{id}/moves` | Make the next human move, then computer replies |
| GET | `/games/{id}/moves` | List all recorded moves in chronological order |
| POST | `/games/{id}/coach` | Get AI coaching recommendation |
| DELETE | `/games/{id}` | Delete a game |

### Move Contract

- `POST /games/{id}/moves` accepts 0-based coordinates:
  - request body: `{"x": 0..2, "y": 0..2}`
  - coordinates map to internal position with `position = y * 3 + x`
- Human moves first, then the computer makes its move automatically (first available empty cell).

### Board Representation

- API responses use a flat 9-cell board array:
  - `[".", ".", ".", ".", ".", ".", ".", ".", "."]`
  - empty cells are `"."`, occupied cells are `"X"` or `"O"`
- This representation is intentionally kept for simpler frontend rendering.

### Example

```bash
# Create a game
curl -X POST http://localhost:8000/games

# Human move at top-left (x=0, y=0); response includes computer move too
curl -X POST http://localhost:8000/games/{id}/moves \
  -H "Content-Type: application/json" \
  -d '{"x": 0, "y": 0}'
```

Internal positions are numbered 0–8, left to right, top to bottom:

```
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

## Assumptions and Tradeoffs

- No authentication: "games I have played" is interpreted as all games in the database.
- Game list and move history are returned oldest-first (chronological ascending).
- Computer strategy picks a random available empty cell, favoring simplicity over stronger play.
- Data is persisted in SQLite via SQLAlchemy async ORM with Alembic managing schema migrations.

## Extra features

- Single-page UI in `index.html`
- AI coach endpoint (`POST /games/{id}/coach`)

## Configuration

The application uses environment variables for configuration. You can provide them directly or via a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./tic_tac_toe.db` | SQLAlchemy connection string |
| `ANTHROPIC_API_KEY` | (required for coaching) | API key for AI coaching |
| `AI_COACH_MODEL` | `claude-haiku-4-5` | Claude model for AI coaching |

## Database

### SQLite (Default)
By default, the app uses a local SQLite database file `tic_tac_toe.db`.

### PostgreSQL
You can swap the storage backend to PostgreSQL. A `docker-compose.yml` is provided for local development.

1. **Start PostgreSQL:**
   ```bash
   docker compose up -d
   ```
2. **Run with PostgreSQL:**
   ```bash
   export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/tic-tac-toe"
   make migrate
   uv run python main.py
   ```

## Database Migrations

Schema changes are managed with [Alembic](https://alembic.sqlalchemy.org/).

```bash
# Apply all pending migrations (run on each deploy)
make migrate

# Generate a new migration after changing app/models.py
make migration MSG="add users table"
```

> **Note:** `init_db()` (which calls `create_all`) is kept for test isolation only.
> Never use `create_all` in production — always apply migrations via `make migrate`.

## Tests

```bash
uv run pytest
```
