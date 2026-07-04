"""Factory for ReportRepository — selects Cosmos or Local (RADAR_OFFLINE) per R9/config."""

from __future__ import annotations

from radar.config import get_settings
from radar.storage.base import ReportRepository

__all__ = ["ReportRepository", "get_repository"]

_repository: ReportRepository | None = None


def get_repository() -> ReportRepository:
    global _repository
    if _repository is not None:
        return _repository

    settings = get_settings()
    if settings.radar_offline:
        from radar.storage.local import LocalReportRepository

        _repository = LocalReportRepository()
    else:
        from radar.storage.cosmos import CosmosReportRepository

        _repository = CosmosReportRepository(
            endpoint=settings.cosmos_endpoint, key=settings.cosmos_key
        )
    return _repository
