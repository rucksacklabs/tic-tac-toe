"""
Purpose: Tests for the metrics infrastructure.
Architecture: Testing Layer (Unit + Integration).
Notes: Uses RecordingMetricsClient to verify business events and middleware recording.
"""

from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.metrics import MetricsClient, NoOpMetricsClient, MetricsMiddleware
from app.dependency_injection import get_metrics, get_ai_coach, get_game_repo
from app.services.ai_coach import AICoach, AICoachError
from app.persistence.in_memory_game_repository import InMemoryGameRepository
from main import app


# ---------------------------------------------------------------------------
# RecordingMetricsClient — test double that captures all calls
# ---------------------------------------------------------------------------


class RecordingMetricsClient:
    def __init__(self):
        self.increments: list[tuple[str, dict]] = []
        self.timings: list[tuple[str, float, dict]] = []
        self.gauges: list[tuple[str, float, dict]] = []

    def increment(self, name: str, tags: dict[str, str] = {}) -> None:
        self.increments.append((name, tags))

    def timing(self, name: str, value_ms: float, tags: dict[str, str] = {}) -> None:
        self.timings.append((name, value_ms, tags))

    def gauge(self, name: str, value: float, tags: dict[str, str] = {}) -> None:
        self.gauges.append((name, value, tags))

    def increment_names(self) -> list[str]:
        return [name for name, _ in self.increments]

    def timing_names(self) -> list[str]:
        return [name for name, _, _ in self.timings]


@pytest.fixture
def recording_metrics():
    return RecordingMetricsClient()


@pytest.fixture
def repo():
    return InMemoryGameRepository()


@pytest.fixture
async def client(repo, recording_metrics):
    app.dependency_overrides[get_game_repo] = lambda: repo
    app.dependency_overrides[get_metrics] = lambda: recording_metrics
    app.state.metrics = recording_metrics
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.pop(get_game_repo, None)
    app.dependency_overrides.pop(get_metrics, None)


def mock_coach_override(recommendation=((1, 1), "Play the center!")):
    coach = AsyncMock(spec=AICoach)
    coach.get_ai_coach_recommendation = AsyncMock(return_value=recommendation)
    return lambda: coach


def error_coach_override(error=AICoachError("provider down")):
    coach = AsyncMock(spec=AICoach)
    coach.get_ai_coach_recommendation = AsyncMock(side_effect=error)
    return lambda: coach


# ---------------------------------------------------------------------------
# Unit tests: NoOpMetricsClient
# ---------------------------------------------------------------------------


def test_noop_implements_protocol():
    client = NoOpMetricsClient()
    client.increment("some.metric")
    client.increment("some.metric", tags={"k": "v"})
    client.timing("some.timer", 42.0)
    client.timing("some.timer", 42.0, tags={"k": "v"})
    client.gauge("some.gauge", 1.0)
    client.gauge("some.gauge", 1.0, tags={"k": "v"})


def test_noop_returns_none():
    client = NoOpMetricsClient()
    assert client.increment("x") is None
    assert client.timing("x", 1.0) is None
    assert client.gauge("x", 1.0) is None


# ---------------------------------------------------------------------------
# Unit tests: RecordingMetricsClient itself
# ---------------------------------------------------------------------------


def test_recording_client_captures_increments():
    m = RecordingMetricsClient()
    m.increment("a")
    m.increment("b", tags={"k": "v"})
    assert m.increment_names() == ["a", "b"]
    assert m.increments[1] == ("b", {"k": "v"})


def test_recording_client_captures_timings():
    m = RecordingMetricsClient()
    m.timing("latency", 99.5, tags={"method": "GET"})
    assert m.timings[0] == ("latency", 99.5, {"method": "GET"})


# ---------------------------------------------------------------------------
# Integration tests: middleware records HTTP metrics
# ---------------------------------------------------------------------------


async def test_middleware_records_request_count(client, recording_metrics):
    await client.post("/games")
    assert "http.request.count" in recording_metrics.increment_names()


async def test_middleware_records_request_duration(client, recording_metrics):
    await client.post("/games")
    assert "http.request.duration_ms" in recording_metrics.timing_names()


async def test_middleware_tags_include_method_and_path(client, recording_metrics):
    await client.post("/games")
    _, tags = next(
        (name, tags)
        for name, tags in recording_metrics.increments
        if name == "http.request.count"
    )
    assert tags["method"] == "POST"
    assert tags["endpoint"] == "/games"
    assert "status_code" in tags


async def test_middleware_tags_include_status_code(client, recording_metrics):
    await client.post("/games")
    _, tags = next(
        (name, tags)
        for name, tags in recording_metrics.increments
        if name == "http.request.count"
    )
    assert tags["status_code"] == "201"


# ---------------------------------------------------------------------------
# Integration tests: business event metrics
# ---------------------------------------------------------------------------


async def test_create_game_records_metric(client, recording_metrics):
    await client.post("/games")
    assert "game.created" in recording_metrics.increment_names()


async def test_delete_game_records_metric(client, recording_metrics):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]
    await client.delete(f"/games/{game_id}")
    assert "game.deleted" in recording_metrics.increment_names()


async def test_make_move_records_game_move_metric(client, recording_metrics):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]
    await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
    assert "game.move" in recording_metrics.increment_names()


async def test_make_move_outcome_tag_present(client, recording_metrics):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]
    await client.post(f"/games/{game_id}/moves", json={"x": 0, "y": 0})
    _, tags = next(
        (name, tags)
        for name, tags in recording_metrics.increments
        if name == "game.move"
    )
    assert tags["outcome"] in ("none", "x_wins", "o_wins", "draw")


async def test_ai_coach_records_request_metric(client, recording_metrics):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]

    app.dependency_overrides[get_ai_coach] = mock_coach_override()
    try:
        await client.post(f"/games/{game_id}/coach")
    finally:
        app.dependency_overrides.pop(get_ai_coach, None)

    assert "ai_coach.request" in recording_metrics.increment_names()


async def test_ai_coach_records_duration_metric(client, recording_metrics):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]

    app.dependency_overrides[get_ai_coach] = mock_coach_override()
    try:
        await client.post(f"/games/{game_id}/coach")
    finally:
        app.dependency_overrides.pop(get_ai_coach, None)

    assert "ai_coach.duration_ms" in recording_metrics.timing_names()


async def test_ai_coach_records_error_metric(client, recording_metrics):
    create_resp = await client.post("/games")
    game_id = create_resp.json()["id"]

    app.dependency_overrides[get_ai_coach] = error_coach_override()
    try:
        response = await client.post(f"/games/{game_id}/coach")
    finally:
        app.dependency_overrides.pop(get_ai_coach, None)

    assert response.status_code == 502
    assert "ai_coach.error" in recording_metrics.increment_names()
    _, tags = next(
        (name, tags)
        for name, tags in recording_metrics.increments
        if name == "ai_coach.error"
    )
    assert tags["error_type"] == "AICoachError"


# ---------------------------------------------------------------------------
# DI override propagation
# ---------------------------------------------------------------------------


async def test_di_override_propagates(client, recording_metrics):
    """Swapping get_metrics in DI overrides propagates to both middleware and route handlers."""
    await client.post("/games")
    # Both middleware (via app.state) and route handler (via Depends) should
    # have recorded metrics on the same RecordingMetricsClient.
    assert len(recording_metrics.increments) >= 2  # http.request.count + game.created
