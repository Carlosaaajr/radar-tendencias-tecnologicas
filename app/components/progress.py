"""Progresso da análise por etapa (FR-008)."""

from __future__ import annotations

import streamlit as st

from radar.orchestrator import ProgressEvent

_STAGE_LABELS = {
    "academic": "Coleta acadêmica (arXiv, OpenAlex)",
    "market": "Coleta de mercado (Agente Coletor, 4 perspectivas)",
    "synthesis": "Consolidação (Agente Sintetizador)",
    "grading": "Cálculo do grau de suporte",
    "saving": "Salvando relatório",
}

_STAGE_ORDER = ("academic", "market", "synthesis", "grading", "saving")


class ProgressTracker:
    """Mantém um placeholder Streamlit atualizado conforme os ProgressEvents chegam."""

    def __init__(self) -> None:
        self._placeholder = st.empty()
        self._status: dict[str, tuple[str, bool]] = {}

    def handle_event(self, event: ProgressEvent) -> None:
        self._status[event.stage] = (event.detail, event.done)
        self._render()

    def _render(self) -> None:
        with self._placeholder.container():
            for stage in _STAGE_ORDER:
                label = _STAGE_LABELS[stage]
                if stage not in self._status:
                    st.markdown(f"⏳ {label}")
                    continue
                detail, done = self._status[stage]
                icon = "✅" if done else "🔄"
                st.markdown(f"{icon} **{label}** — {detail}")
