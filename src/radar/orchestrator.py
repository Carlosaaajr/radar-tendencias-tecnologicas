"""Orquestrador do pipeline (contracts §6) — coleta → síntese → graduação → persistência."""

from __future__ import annotations

import asyncio
import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from radar.agents.collector_agent import run_market_collection
from radar.agents.scope_guard import ScopeCheckError, is_in_scope
from radar.agents.synthesizer_agent import synthesize
from radar.collectors.arxiv import ArxivCollector
from radar.collectors.openalex import OpenAlexCollector
from radar.config import get_settings
from radar.models import Report, ReportStatus
from radar.storage import get_repository
from radar.synthesis.dedup import dedup_evidence
from radar.synthesis.grading import grade_report

MIN_EVIDENCE_FOR_CONFIDENT_REPORT = 5
SCOPE_CHECK_TIMEOUT_S = 15


class RateLimitExceeded(Exception):
    """Limite diário de análises (MAX_ANALYSES_PER_DAY, R10) atingido."""


class OutOfScopeError(Exception):
    """Tema não parece ser uma tendência tecnológica/industrial (guardrail de escopo)."""


@dataclass
class ProgressEvent:
    stage: Literal["academic", "market", "synthesis", "grading", "saving"]
    detail: str
    done: bool = False


def slugify(theme: str) -> str:
    normalized = unicodedata.normalize("NFKD", theme).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")
    return slug or "tema"


def _check_daily_limit() -> None:
    settings = get_settings()
    repo = get_repository()
    today = datetime.now(UTC).date()
    count_today = sum(
        1 for s in repo.list_summaries() if s.created_at.date() == today
    )
    if count_today >= settings.max_analyses_per_day:
        raise RateLimitExceeded(
            f"Limite diário de {settings.max_analyses_per_day} análises atingido. "
            "Tente novamente amanhã ou consulte o histórico de relatórios já gerados."
        )


async def run_analysis(
    theme: str,
    *,
    on_progress: Callable[[ProgressEvent], None] | None = None,
    budget_s: float | None = None,
) -> Report:
    def emit(stage: str, detail: str, done: bool = False) -> None:
        if on_progress:
            on_progress(ProgressEvent(stage=stage, detail=detail, done=done))

    _check_daily_limit()

    try:
        in_scope = await asyncio.wait_for(is_in_scope(theme), timeout=SCOPE_CHECK_TIMEOUT_S)
    except (TimeoutError, ScopeCheckError):
        # Falha do classificador nunca bloqueia uma análise legítima (Princípio IV) —
        # fail-open: segue como se estivesse dentro de escopo.
        in_scope = True
    if not in_scope:
        raise OutOfScopeError(
            f'O tema "{theme}" não parece ser uma tendência tecnológica ou industrial. '
            'Tente reformular (ex.: "Edge AI", "Robôs Humanoides para Indústria").'
        )

    settings = get_settings()
    budget = budget_s if budget_s is not None else settings.analysis_budget_seconds
    repo = get_repository()

    report = Report(theme=theme, theme_slug=slugify(theme), status=ReportStatus.RUNNING)
    repo.save(report)

    degraded_sources: list[str] = []
    warnings: list[str] = []

    async def collect_academic() -> list:
        emit("academic", "Consultando arXiv e OpenAlex...")
        results = await asyncio.gather(
            ArxivCollector().collect(theme),
            OpenAlexCollector().collect(theme),
            return_exceptions=True,
        )
        evidence = []
        for name, result in zip(("arXiv", "OpenAlex"), results, strict=True):
            if isinstance(result, BaseException):
                degraded_sources.append(name)
                continue
            if result.degraded:
                degraded_sources.append(name)
            evidence.extend(result.evidence)
        emit("academic", f"{len(evidence)} evidências acadêmicas coletadas", done=True)
        return evidence

    async def collect_market() -> list:
        emit("market", "Perguntando ao Agente Coletor (4 perspectivas)...")
        result = await run_market_collection(theme)
        if result.degraded:
            degraded_sources.append("mercado (Web Search)")
        emit("market", f"{len(result.evidence)} evidências de mercado coletadas", done=True)
        return result.evidence

    try:
        academic_evidence, market_evidence = await asyncio.wait_for(
            asyncio.gather(collect_academic(), collect_market()), timeout=budget * 0.7
        )
    except TimeoutError:
        report.status = ReportStatus.PARTIAL
        report.warnings.append("Tempo limite atingido durante a coleta; relatório parcial.")
        repo.save(report)
        return report

    combined = academic_evidence + market_evidence
    for i, ev in enumerate(combined, start=1):
        ev.id = f"ev-{i}"

    deduped = dedup_evidence(combined)
    corpus_by_id = {ev.id: ev for ev in deduped}

    if not deduped:
        report.status = ReportStatus.FAILED
        report.degraded_sources = degraded_sources
        report.warnings.append("Nenhuma evidência coletada em nenhuma fonte.")
        repo.save(report)
        return report

    if len(deduped) < MIN_EVIDENCE_FOR_CONFIDENT_REPORT:
        warnings.append(
            f"Baixa sustentação: apenas {len(deduped)} evidências encontradas para o tema."
        )

    try:
        emit("synthesis", "Consolidando painel executivo...")
        synthesis_result = await asyncio.wait_for(
            synthesize(theme, deduped), timeout=budget * 0.4
        )
        emit("synthesis", "Painel consolidado", done=True)
    except Exception as exc:  # noqa: BLE001 — falha da API do Foundry (timeout,
        # SynthesisError, RateLimitError etc.) nunca pode derrubar a análise (FR-013)
        report.status = ReportStatus.PARTIAL
        report.evidence = deduped
        report.degraded_sources = degraded_sources
        report.warnings = warnings + [f"Falha na síntese: {exc}"]
        repo.save(report)
        return report

    emit("grading", "Calculando grau de suporte por seção...")
    graded_sections = grade_report(synthesis_result.sections, corpus_by_id)
    emit("grading", "Grau de suporte calculado", done=True)

    report.status = ReportStatus.COMPLETED
    report.scope_note = synthesis_result.scope_note
    report.sections = graded_sections
    report.evidence = deduped
    report.degraded_sources = degraded_sources
    report.warnings = warnings + synthesis_result.raw_warnings

    emit("saving", "Salvando relatório...")
    repo.save(report)
    emit("saving", "Relatório salvo", done=True)

    return report
