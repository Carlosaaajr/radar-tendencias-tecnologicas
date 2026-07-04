"""Exploração de evidências com filtros por tipo de fonte (FR-015, US3)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from radar.models import SourceType  # noqa: E402
from radar.storage import get_repository  # noqa: E402

st.set_page_config(page_title="Evidências — Radar de Tendências", page_icon="🔎", layout="wide")
st.title("🔎 Exploração de evidências")

report = st.session_state.get("current_report")

if report is None:
    repo = get_repository()
    summaries = repo.list_summaries()
    if not summaries:
        st.info(
            "Nenhum relatório disponível ainda. Gere um painel na página inicial primeiro."
        )
    else:
        st.caption("Nenhum relatório ativo na sessão — selecione um do histórico:")
        options = {f"{s.theme} ({s.created_at.strftime('%d/%m/%Y %H:%M')})": s for s in summaries}
        choice = st.selectbox("Relatório", list(options.keys()))
        summary = options[choice]
        report = repo.get(summary.id, summary.theme_slug)

if report is None:
    st.warning("Selecione um relatório para explorar as evidências.")
else:
    st.subheader(report.theme)

    counts_by_type = {st_: 0 for st_ in SourceType}
    for ev in report.evidence:
        counts_by_type[ev.source_type] += 1

    labels = {
        SourceType.SCIENTIFIC: "Científica",
        SourceType.MARKET: "Mercado/Consultoria",
        SourceType.NEWS: "Notícia",
        SourceType.CORPORATE: "Corporativa",
        SourceType.PATENT: "Patente",
    }

    options = ["Todas"] + [
        f"{labels[st_]} ({counts_by_type[st_]})" for st_ in SourceType if counts_by_type[st_] > 0
    ]
    selected = st.radio("Filtrar por tipo de fonte", options, horizontal=True)

    if selected == "Todas":
        filtered = report.evidence
    else:
        selected_label = selected.rsplit(" (", 1)[0]
        selected_type = next(st_ for st_, label in labels.items() if label == selected_label)
        filtered = [ev for ev in report.evidence if ev.source_type == selected_type]

    st.caption(f"{len(filtered)} de {len(report.evidence)} evidências")

    for ev in filtered:
        with st.container(border=True):
            st.markdown(f"**[{ev.title}]({ev.url})**")
            date_part = f" · {ev.published_at}" if ev.published_at else ""
            st.caption(f"{labels[ev.source_type]} · {ev.origin}{date_part} · idioma: {ev.language}")
            if ev.snippet:
                st.write(ev.snippet)

    divergent_sections = [s for s in report.sections if s.divergence_note]
    if divergent_sections:
        st.divider()
        st.subheader("Divergências entre fontes")
        for section in divergent_sections:
            st.warning(f"**{section.key}**: {section.divergence_note}")
