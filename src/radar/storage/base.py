"""ReportRepository protocol (contracts §7) — implemented by Cosmos and Local repos."""

from __future__ import annotations

from typing import Protocol

from radar.models import Report, ReportSummary


class ReportRepository(Protocol):
    def save(self, report: Report) -> None: ...

    def get(self, report_id: str, theme_slug: str) -> Report | None: ...

    def list_summaries(self) -> list[ReportSummary]: ...

    def find_by_slug(self, theme_slug: str) -> list[ReportSummary]: ...
