"""
Purpose: Protocol definition for metrics clients.
Architecture: Infrastructure Layer (Metrics Abstraction).
Notes: Defines the MetricsClient interface. Swap NoOpMetricsClient for any backend
       in dependency_injection.py without changing call sites.
"""

from typing import Protocol


class MetricsClient(Protocol):
    def increment(self, name: str, tags: dict[str, str] = {}) -> None: ...
    def timing(self, name: str, value_ms: float, tags: dict[str, str] = {}) -> None: ...
    def gauge(self, name: str, value: float, tags: dict[str, str] = {}) -> None: ...
