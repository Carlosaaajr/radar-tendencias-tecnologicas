import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from radar.collectors.base import CollectorResult
from radar.models import Evidence, ReportStatus, SourceType
from radar.orchestrator import OutOfScopeError, RateLimitExceeded, run_analysis

TMP_DIR = Path("tests/fixtures/_tmp_pipeline_repo")


def _ev(id_: str, source_type: SourceType = SourceType.NEWS) -> Evidence:
    return Evidence(
        id=id_,
        title=f"Title {id_}",
        source_type=source_type,
        origin="origin",
        url=f"https://example.com/{id_}",
        snippet="snippet",
        language="en",
    )


VALID_SYNTHESIS_RAW = {
    "sections": [
        {
            "key": "definition",
            "content_md": "Definição com citação [ev-1].",
            "evidence_ids": ["ev-1"],
            "is_inference": False,
            "divergence_note": None,
        },
        {
            "key": "outlook",
            "content_md": "Inferência sem lastro direto.",
            "evidence_ids": [],
            "is_inference": True,
            "divergence_note": None,
        },
    ],
    "scope_note": None,
}


@pytest.fixture(autouse=True)
def local_repo(monkeypatch):
    if TMP_DIR.exists():
        shutil.rmtree(TMP_DIR)
    from radar.storage.local import LocalReportRepository

    repo = LocalReportRepository(data_dir=TMP_DIR)
    monkeypatch.setattr("radar.orchestrator.get_repository", lambda: repo)
    yield repo
    shutil.rmtree(TMP_DIR, ignore_errors=True)


@pytest.fixture(autouse=True)
def default_in_scope(monkeypatch):
    """Por padrão todo tema é aceito nos testes — os testes do guardrail sobrescrevem isso."""
    monkeypatch.setattr("radar.orchestrator.is_in_scope", AsyncMock(return_value=True))


def _patch_synthesize(raw: dict = VALID_SYNTHESIS_RAW):
    from radar.agents.synthesizer_agent import parse_synthesis_output

    async def fake_synthesize(theme, corpus, *, timeout_s=120):
        corpus_by_id = {ev.id: ev for ev in corpus}
        return parse_synthesis_output(raw, corpus_by_id)

    return patch("radar.orchestrator.synthesize", side_effect=fake_synthesize)


@pytest.mark.asyncio
async def test_happy_path_completes_with_all_sources_ok():
    academic = CollectorResult(evidence=[_ev("ev-101", SourceType.SCIENTIFIC), _ev("ev-102", SourceType.SCIENTIFIC)])
    market = CollectorResult(evidence=[_ev("ev-201", SourceType.MARKET), _ev("ev-202", SourceType.NEWS)])

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=market)),
        _patch_synthesize(),
    ):
        MockArxiv.return_value.collect = AsyncMock(return_value=academic)
        MockOpenAlex.return_value.collect = AsyncMock(
            return_value=CollectorResult(evidence=[])
        )

        report = await run_analysis("Edge AI")

    assert report.status == ReportStatus.COMPLETED
    assert report.degraded_sources == []
    assert len(report.sections) == 2


@pytest.mark.asyncio
async def test_one_source_degraded_still_completes():
    academic_ok = CollectorResult(evidence=[_ev("ev-101", SourceType.SCIENTIFIC)])
    academic_degraded = CollectorResult(evidence=[], degraded=True, error="timeout")
    market = CollectorResult(evidence=[_ev("ev-201", SourceType.MARKET)])

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=market)),
        _patch_synthesize(),
    ):
        MockArxiv.return_value.collect = AsyncMock(return_value=academic_degraded)
        MockOpenAlex.return_value.collect = AsyncMock(return_value=academic_ok)

        report = await run_analysis("Edge AI")

    assert report.status == ReportStatus.COMPLETED
    assert "arXiv" in report.degraded_sources


@pytest.mark.asyncio
async def test_raw_exception_in_one_academic_collector_still_completes():
    """Regressao: excecao crua (nao CollectorResult.degraded) em uma fonte academica
    nao pode abortar a analise inteira (achado H2 da revisao de codigo)."""
    academic_ok = CollectorResult(evidence=[_ev("ev-101", SourceType.SCIENTIFIC)])
    market = CollectorResult(evidence=[_ev("ev-201", SourceType.MARKET)])

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=market)),
        _patch_synthesize(),
    ):
        MockArxiv.return_value.collect = AsyncMock(side_effect=AttributeError("boom"))
        MockOpenAlex.return_value.collect = AsyncMock(return_value=academic_ok)

        report = await run_analysis("Edge AI")

    assert report.status == ReportStatus.COMPLETED
    assert "arXiv" in report.degraded_sources


@pytest.mark.asyncio
async def test_market_fully_degraded_academic_ok_still_completes():
    academic = CollectorResult(evidence=[_ev("ev-101", SourceType.SCIENTIFIC), _ev("ev-102", SourceType.SCIENTIFIC)])
    market_degraded = CollectorResult(evidence=[], degraded=True, error="all perspectives failed")

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=market_degraded)),
        _patch_synthesize(),
    ):
        MockArxiv.return_value.collect = AsyncMock(return_value=academic)
        MockOpenAlex.return_value.collect = AsyncMock(return_value=CollectorResult(evidence=[]))

        report = await run_analysis("Edge AI")

    assert report.status == ReportStatus.COMPLETED
    assert "mercado (Web Search)" in report.degraded_sources


@pytest.mark.asyncio
async def test_synthesis_api_error_yields_partial_not_crash():
    """Regressao: erro de API do Foundry na sintese (ex.: RateLimitError 429, achado
    real do smoke test T036) MUST virar status=partial, nunca propagar sem tratamento."""
    academic = CollectorResult(evidence=[_ev("ev-101", SourceType.SCIENTIFIC)])
    market = CollectorResult(evidence=[_ev("ev-201", SourceType.MARKET)])

    async def failing_synthesize(theme, corpus, *, timeout_s=120):
        raise RuntimeError("Model deployment rate limit exceeded")

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=market)),
        patch("radar.orchestrator.synthesize", side_effect=failing_synthesize),
    ):
        MockArxiv.return_value.collect = AsyncMock(return_value=academic)
        MockOpenAlex.return_value.collect = AsyncMock(return_value=CollectorResult(evidence=[]))

        report = await run_analysis("Edge AI")

    assert report.status == ReportStatus.PARTIAL
    assert any("Falha na síntese" in w for w in report.warnings)


@pytest.mark.asyncio
async def test_all_sources_degraded_fails():
    empty_degraded = CollectorResult(evidence=[], degraded=True, error="down")

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=empty_degraded)),
    ):
        MockArxiv.return_value.collect = AsyncMock(return_value=empty_degraded)
        MockOpenAlex.return_value.collect = AsyncMock(return_value=empty_degraded)

        report = await run_analysis("Tema Totalmente Obscuro")

    assert report.status == ReportStatus.FAILED


@pytest.mark.asyncio
async def test_timeout_during_collection_yields_partial():
    async def slow_collect(*args, **kwargs):
        import asyncio

        await asyncio.sleep(5)
        return CollectorResult(evidence=[_ev("ev-1")])

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(side_effect=slow_collect)),
    ):
        MockArxiv.return_value.collect = AsyncMock(side_effect=slow_collect)
        MockOpenAlex.return_value.collect = AsyncMock(return_value=CollectorResult(evidence=[]))

        report = await run_analysis("Edge AI", budget_s=0.5)

    assert report.status == ReportStatus.PARTIAL


@pytest.mark.asyncio
async def test_daily_rate_limit_enforced(monkeypatch):
    monkeypatch.setenv("MAX_ANALYSES_PER_DAY", "0")
    from radar.config import get_settings

    get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None
    import radar.config as config_module

    config_module._settings = None

    with pytest.raises(RateLimitExceeded):
        await run_analysis("Edge AI")

    config_module._settings = None


@pytest.mark.asyncio
async def test_out_of_scope_theme_raises_and_persists_nothing(monkeypatch, local_repo):
    """Guardrail de escopo: tema fora de contexto nunca chega a rodar o pipeline caro
    nem a poluir o historico com um relatorio."""
    monkeypatch.setattr("radar.orchestrator.is_in_scope", AsyncMock(return_value=False))

    with pytest.raises(OutOfScopeError):
        await run_analysis("qual a capital da frança?")

    assert local_repo.list_summaries() == []


@pytest.mark.asyncio
async def test_scope_check_failure_fails_open_and_completes(monkeypatch):
    """Se o classificador de escopo falhar (rede/API), a analise MUST prosseguir
    normalmente — nunca bloquear um tema legitimo por falha de um checador auxiliar
    (Principio IV)."""
    from radar.agents.scope_guard import ScopeCheckError

    monkeypatch.setattr(
        "radar.orchestrator.is_in_scope", AsyncMock(side_effect=ScopeCheckError("boom"))
    )
    academic = CollectorResult(evidence=[_ev("ev-101", SourceType.SCIENTIFIC)])
    market = CollectorResult(evidence=[_ev("ev-201", SourceType.MARKET)])

    with (
        patch("radar.orchestrator.ArxivCollector") as MockArxiv,
        patch("radar.orchestrator.OpenAlexCollector") as MockOpenAlex,
        patch("radar.orchestrator.run_market_collection", new=AsyncMock(return_value=market)),
        _patch_synthesize(),
    ):
        MockArxiv.return_value.collect = AsyncMock(return_value=academic)
        MockOpenAlex.return_value.collect = AsyncMock(return_value=CollectorResult(evidence=[]))

        report = await run_analysis("Edge AI")

    assert report.status == ReportStatus.COMPLETED
