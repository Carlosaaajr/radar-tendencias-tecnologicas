"""Página principal: informar tema → gerar painel executivo (US1, FR-001/008)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from components.panel import render_report  # noqa: E402
from components.progress import ProgressTracker  # noqa: E402

from radar.models import ReportStatus  # noqa: E402
from radar.orchestrator import RateLimitExceeded, run_analysis  # noqa: E402

st.set_page_config(page_title="Radar de Tendências Tecnológicas", page_icon="📡", layout="wide")

if "running_analysis" not in st.session_state:
    st.session_state.running_analysis = False
if "current_report" not in st.session_state:
    st.session_state.current_report = None

st.title("📡 Radar de Tendências Tecnológicas")
st.caption(
    "Informe uma tendência, tecnologia ou conceito de interesse e receba um painel "
    "executivo fundamentado em evidências verificáveis."
)

theme = st.text_input(
    "Tema de interesse",
    placeholder='Ex.: "Edge AI" ou "Robôs Humanoides para Indústria"',
    disabled=st.session_state.running_analysis,
)

start = st.button(
    "Gerar painel",
    type="primary",
    disabled=st.session_state.running_analysis or not theme.strip(),
)

if start:
    st.session_state.running_analysis = True
    st.session_state.current_report = None

    tracker = ProgressTracker()
    try:
        report = asyncio.run(run_analysis(theme.strip(), on_progress=tracker.handle_event))
        st.session_state.current_report = report
    except RateLimitExceeded as exc:
        st.error(f"🚫 {exc}")
    except Exception as exc:  # noqa: BLE001 — falha inesperada, nunca deve travar a UI
        st.error(f"❌ A análise falhou de forma inesperada: {exc}")
    finally:
        st.session_state.running_analysis = False

report = st.session_state.current_report
if report is not None:
    if report.status == ReportStatus.FAILED:
        st.error(
            "❌ Não foi possível concluir a análise: nenhuma evidência foi coletada em "
            "nenhuma fonte disponível."
        )
        for warning in report.warnings:
            st.caption(warning)
        st.info("Consulte o histórico de relatórios já gerados na página **Histórico**.")
    else:
        render_report(report)
