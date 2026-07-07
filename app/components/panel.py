"""Render do painel executivo — 10 seções + badges de suporte (FR-004/005/006, SC-006)."""

from __future__ import annotations

import streamlit as st
from components.charts import render_overview_charts

from radar.models import Report, ReportStatus, SupportLevel

_SECTION_LABELS = {
    "definition": "Definição do tema",
    "maturity": "Nível de maturidade",
    "applications": "Principais aplicações",
    "sectors": "Setores impactados",
    "players": "Empresas e instituições relevantes",
    "investments": "Investimentos e movimentos de mercado",
    "adoption_signals": "Sinais de adoção",
    "opportunities": "Oportunidades",
    "risks": "Desafios e riscos",
    "outlook": "Perspectivas futuras",
}

_LEVEL_BADGE = {
    SupportLevel.HIGH: "🟢 Alto suporte",
    SupportLevel.MEDIUM: "🟡 Suporte médio",
    SupportLevel.LOW: "🟠 Suporte baixo",
    SupportLevel.INFERENCE: "⚪ Inferência analítica",
}


def render_report(report: Report) -> None:
    st.subheader(f"Painel executivo — {report.theme}")

    if report.status == ReportStatus.PARTIAL:
        st.warning("⚠️ Este relatório é parcial — a análise não foi concluída totalmente.")
    if report.scope_note:
        st.info(f"Recorte adotado: {report.scope_note}")
    if report.degraded_sources:
        st.warning(
            "As seguintes categorias de fonte ficaram indisponíveis nesta execução: "
            + ", ".join(report.degraded_sources)
        )
    for warning in report.warnings:
        st.warning(warning)

    if report.evidence:
        with st.container(border=True):
            render_overview_charts(report.evidence, report.sections)

    evidence_by_id = {ev.id: ev for ev in report.evidence}

    for section in report.sections:
        label = _SECTION_LABELS.get(section.key, section.key)
        with st.container(border=True):
            st.markdown(f"### {label}")

            if section.support is not None:
                badge = _LEVEL_BADGE[section.support.level]
                st.caption(
                    f"{badge} — {section.support.evidence_count} evidência(s), "
                    f"{section.support.source_type_count} tipo(s) de fonte"
                )

            st.markdown(section.content_md)

            if section.divergence_note:
                st.info(f"🔀 Divergência entre fontes: {section.divergence_note}")

            if section.evidence_ids:
                with st.expander(f"Referências ({len(section.evidence_ids)})"):
                    for eid in section.evidence_ids:
                        ev = evidence_by_id.get(eid)
                        if ev is None:
                            continue
                        date_part = f" — {ev.published_at}" if ev.published_at else ""
                        st.markdown(f"- [{ev.title}]({ev.url}){date_part} ({ev.origin})")
            elif section.is_inference:
                st.caption("Sem evidência direta — conteúdo marcado como inferência analítica.")
