"""
Purpose: No-op implementation of MetricsClient.
Architecture: Infrastructure Layer (Metrics).
Notes: Default implementation that silently discards all metrics.
       Replace this in get_metrics() to wire in a real backend.
"""


class NoOpMetricsClient:
    def increment(self, name: str, tags: dict[str, str] = {}) -> None:
        pass

    def timing(self, name: str, value_ms: float, tags: dict[str, str] = {}) -> None:
        pass

    def gauge(self, name: str, value: float, tags: dict[str, str] = {}) -> None:
        pass
