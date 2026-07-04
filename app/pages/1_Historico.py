"""Histórico de relatórios — reabertura instantânea sem nova coleta (FR-009/010)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from components.panel import render_report  # noqa: E402

from radar.models import ReportStatus  # noqa: E402
from radar.storage import get_repository  # noqa: E402

st.set_page_config(page_title="Histórico — Radar de Tendências", page_icon="🗂️", layout="wide")
st.title("🗂️ Histórico de relatórios")

repo = get_repository()

try:
    summaries = repo.list_summaries()
except Exception as exc:  # noqa: BLE001 — histórico deve degradar com mensagem clara
    st.error(f"❌ Não foi possível carregar o histórico: {exc}")
    summaries = []

if not summaries:
    st.info("Nenhum relatório gerado ainda. Volte à página inicial para criar o primeiro.")
else:
    for summary in summaries:
        cols = st.columns([3, 2, 1, 1])
        cols[0].markdown(f"**{summary.theme}**")
        cols[1].caption(summary.created_at.strftime("%d/%m/%Y %H:%M"))

        if summary.status == ReportStatus.PARTIAL:
            cols[2].markdown("⚠️ Parcial")
        elif summary.status == ReportStatus.FAILED:
            cols[2].markdown("❌ Falhou")
        elif summary.status == ReportStatus.RUNNING:
            cols[2].markdown("⏳ Incompleto")
        else:
            cols[2].markdown("✅ Completo")

        if cols[3].button("Abrir", key=f"open-{summary.id}"):
            st.session_state.selected_report_id = summary.id
            st.session_state.selected_theme_slug = summary.theme_slug

    st.divider()

    selected_id = st.session_state.get("selected_report_id")
    selected_slug = st.session_state.get("selected_theme_slug")
    if selected_id:
        report = repo.get(selected_id, selected_slug)
        if report is None:
            st.error("Relatório não encontrado.")
        else:
            st.session_state.current_report = report
            render_report(report)
