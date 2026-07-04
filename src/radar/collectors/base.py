"""Collector protocol + CollectorResult (contracts §1) — graceful degradation only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from radar.models import Evidence, SourceType


@dataclass
class CollectorResult:
    evidence: list[Evidence] = field(default_factory=list)
    degraded: bool = False
    error: str | None = None


class Collector(Protocol):
    name: str
    source_type: SourceType

    async def collect(
        self, theme: str, *, limit: int = 10, timeout_s: float = 30
    ) -> CollectorResult: ...
