"""
Purpose: Entry point for the Tic-Tac-Toe FastAPI application.
Architecture: Application Layer. Initializes the FastAPI app, includes routers, and serves the frontend.
Notes: Uses a lifespan handler to initialize the database and dependencies. Serves index.html from the root.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.persistence.database import init_db
from app.api.games import router as games_router
from app.metrics import MetricsMiddleware
from app.dependency_injection import get_metrics


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Tic-Tac-Toe API", lifespan=lifespan)
app.state.metrics = get_metrics()
app.add_middleware(MetricsMiddleware)
app.include_router(games_router)

# Serve single-file frontend from project root (same origin as API)
INDEX_PATH = Path(__file__).resolve().parent / "index.html"


@app.get("/")
@app.get("/index.html")
def serve_index():
    if not INDEX_PATH.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(INDEX_PATH)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
