"""LocalReportRepository — JSON files on disk (R9: demo offline / RADAR_OFFLINE=1)."""

from __future__ import annotations

import json
from pathlib import Path

from radar.models import Report, ReportSummary, SupportLevel

DEFAULT_DATA_DIR = Path("data/reports")


class LocalReportRepository:
    def __init__(self, data_dir: Path | str = DEFAULT_DATA_DIR) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, report_id: str) -> Path:
        return self.data_dir / f"{report_id}.json"

    def save(self, report: Report) -> None:
        path = self._path(report.id)
        path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    def get(self, report_id: str, theme_slug: str) -> Report | None:
        path = self._path(report_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        report = Report.model_validate(data)
        if report.theme_slug != theme_slug:
            return None
        return report

    def _all_reports(self) -> list[Report]:
        reports = []
        for path in self.data_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                reports.append(Report.model_validate(data))
            except (json.JSONDecodeError, ValueError):
                continue
        return reports

    def list_summaries(self) -> list[ReportSummary]:
        summaries = [_to_summary(r) for r in self._all_reports()]
        return sorted(summaries, key=lambda s: s.created_at, reverse=True)

    def find_by_slug(self, theme_slug: str) -> list[ReportSummary]:
        return [s for s in self.list_summaries() if s.theme_slug == theme_slug]


def _to_summary(report: Report) -> ReportSummary:
    overview: dict[SupportLevel, int] = {}
    for section in report.sections:
        if section.support is None:
            continue
        overview[section.support.level] = overview.get(section.support.level, 0) + 1
    return ReportSummary(
        id=report.id,
        theme=report.theme,
        theme_slug=report.theme_slug,
        created_at=report.created_at,
        status=report.status,
        support_overview=overview,
    )
