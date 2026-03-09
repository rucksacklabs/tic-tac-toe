# Tic-Tac-Toe API

A REST API for multi-session tic-tac-toe built with FastAPI, SQLAlchemy, and SQLite.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
make install
```

## Run

```bash
make run
```

API available at http://localhost:8000
UI available at http://localhost:8000/

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/games` | Create a new game |
| GET | `/games` | List all games in chronological order |
| GET | `/games/{id}` | Get game state |
| POST | `/games/{id}/moves` | Make the next human move, then computer replies |
| GET | `/games/{id}/moves` | List all recorded moves in chronological order |
| GET | `/coach/{id}` | Get AI coaching recommendation |
| DELETE | `/games/{id}` | Delete a game |

### Move Contract

- `POST /games/{id}/moves` accepts 0-based coordinates:
  - request body: `{"x": 0..2, "y": 0..2}`
  - coordinates map to internal position with `position = y * 3 + x`
- Human moves first, then the computer makes its move automatically.

### Board Representation

- API responses use a flat 9-cell board array:
  - `[".", ".", ".", ".", ".", ".", ".", ".", "."]`
  - empty cells are `"."`, occupied cells are `"X"` or `"O"`
- This representation is intentionally kept for simpler frontend rendering.

### Example

```bash
# List all games
curl -X GET http://localhost:8000/games

# Create a game
curl -X POST http://localhost:8000/games

# Human move at top-left (x=0, y=0); response includes computer move too
curl -X POST http://localhost:8000/games/${id}/moves \
  -H "Content-Type: application/json" \
  -d '{"x": 0, "y": 0}'
  
# List past game moves
curl -X GET http://localhost:8000/games/${id}/moves
```

Internally positions are numbered 0–8, left to right, top to bottom:

```
0 | 1 | 2
---------
3 | 4 | 5
---------
6 | 7 | 8
```

## Assumptions, Tradeoffs and Notes

If the service were to stay the way it is now, it could be considered over-engineered. 
Given the goal of this exercise is to have something as production ready as possible, we're assuming this is the starting point of a sprawling tic-tac-toe SaaS platform.
Designing the service to be extensible and maintainable was key in that regard.
Which includes the service logic, swappable persistence, monitoring and a deployment vehicle (docker + helm charts).



Took me about two evenings or 4-ish hours altogether.

Some more assumptions and notes:
- No authentication: "games I have played" is interpreted as all games in the database.
- Game list and move history are returned oldest-first (chronological ascending).
- Computer strategy picks a random available empty cell.
- Data is persisted in SQLite or PostgreSQL via SQLAlchemy async ORM with Alembic managing schema migrations.

## Demos

**UI Demo**

https://github.com/user-attachments/assets/8c328070-e14d-4374-9e0d-71f0466e59ed

**API Demo**

https://github.com/user-attachments/assets/dadc12ac-527b-4b61-846a-8ef5770fcc8a

## Extra features

- Single-page UI in `index.html`
- AI coach endpoint (`GET /coach/{id}`)

The idea is for the coach to take the current game state and well, coach the player by suggesting the next best move.

## Configuration

The application uses environment variables for configuration. You can provide them directly or via a `.env` file.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./tic_tac_toe.db` | SQLAlchemy connection string |
| `OPENAI_API_KEY` | (required for coaching) | API key for AI coaching |
| `AI_COACH_MODEL` | `gpt-4o-mini` | OpenAI model for AI coaching |

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
