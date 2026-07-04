import shutil
from pathlib import Path

import pytest

from radar.models import Report, ReportStatus
from radar.storage.local import LocalReportRepository

TMP_DIR = Path("tests/fixtures/_tmp_local_repo")


@pytest.fixture
def repo():
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    r = LocalReportRepository(data_dir=TMP_DIR)
    yield r
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def _make_report(theme: str, theme_slug: str, status: ReportStatus = ReportStatus.COMPLETED) -> Report:
    return Report(theme=theme, theme_slug=theme_slug, status=status)


def test_save_and_get_point_read(repo):
    report = _make_report("Edge AI", "edge-ai")
    repo.save(report)

    fetched = repo.get(report.id, "edge-ai")
    assert fetched is not None
    assert fetched.id == report.id
    assert fetched.theme == "Edge AI"


def test_get_wrong_theme_slug_returns_none(repo):
    report = _make_report("Edge AI", "edge-ai")
    repo.save(report)

    assert repo.get(report.id, "wrong-slug") is None


def test_get_missing_report_returns_none(repo):
    assert repo.get("nonexistent-id", "edge-ai") is None


def test_list_summaries_sorted_by_created_at_desc(repo):
    r1 = _make_report("Edge AI", "edge-ai")
    r2 = _make_report("Robôs Humanoides", "robos-humanoides")
    repo.save(r1)
    repo.save(r2)

    summaries = repo.list_summaries()
    assert len(summaries) == 2
    assert {s.theme_slug for s in summaries} == {"edge-ai", "robos-humanoides"}


def test_find_by_slug(repo):
    r1 = _make_report("Edge AI", "edge-ai")
    r2 = _make_report("Edge AI", "edge-ai")
    r3 = _make_report("Robôs Humanoides", "robos-humanoides")
    repo.save(r1)
    repo.save(r2)
    repo.save(r3)

    matches = repo.find_by_slug("edge-ai")
    assert len(matches) == 2
    assert all(s.theme_slug == "edge-ai" for s in matches)
