import shutil
from pathlib import Path

import pytest

from radar.models import Report, ReportStatus
from radar.storage.local import LocalReportRepository

TMP_DIR = Path("tests/fixtures/_tmp_history_repo")


@pytest.fixture
def repo():
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    r = LocalReportRepository(data_dir=TMP_DIR)
    yield r
    shutil.rmtree(TMP_DIR, ignore_errors=True)


def test_save_list_reopen_roundtrip(repo):
    """US2: salvar -> listar no historico -> reabrir sem nova coleta (FR-009/010)."""
    report = Report(theme="Edge AI", theme_slug="edge-ai", status=ReportStatus.COMPLETED)
    repo.save(report)

    summaries = repo.list_summaries()
    assert len(summaries) == 1
    assert summaries[0].theme == "Edge AI"

    reopened = repo.get(summaries[0].id, summaries[0].theme_slug)
    assert reopened is not None
    assert reopened.id == report.id
    assert reopened.status == ReportStatus.COMPLETED


def test_find_by_slug_offers_reopen_choice_for_repeated_theme(repo):
    """US1 cenário FR-011: tema repetido -> multiplos relatorios encontrados por slug."""
    first = Report(theme="Edge AI", theme_slug="edge-ai", status=ReportStatus.COMPLETED)
    second = Report(theme="Edge AI", theme_slug="edge-ai", status=ReportStatus.COMPLETED)
    other = Report(theme="Robôs Humanoides", theme_slug="robos-humanoides", status=ReportStatus.COMPLETED)
    repo.save(first)
    repo.save(second)
    repo.save(other)

    matches = repo.find_by_slug("edge-ai")
    assert len(matches) == 2
    assert all(m.theme_slug == "edge-ai" for m in matches)

    reopened = repo.get(matches[0].id, matches[0].theme_slug)
    assert reopened is not None


def test_partial_report_visible_in_history_with_status(repo):
    partial = Report(theme="Tema Obscuro", theme_slug="tema-obscuro", status=ReportStatus.PARTIAL)
    repo.save(partial)

    summaries = repo.list_summaries()
    assert summaries[0].status == ReportStatus.PARTIAL


def test_history_open_completes_without_network_dependency(repo):
    """Reabrir do historico nao deve exigir nenhuma chamada de rede (Principio IV)."""
    report = Report(theme="Edge AI", theme_slug="edge-ai", status=ReportStatus.COMPLETED)
    repo.save(report)

    # Uma segunda instância do repositório simula reabrir a app sem rede/sessão anterior
    fresh_repo = LocalReportRepository(data_dir=TMP_DIR)
    summaries = fresh_repo.list_summaries()
    reopened = fresh_repo.get(summaries[0].id, summaries[0].theme_slug)

    assert reopened is not None
    assert reopened.theme == "Edge AI"
