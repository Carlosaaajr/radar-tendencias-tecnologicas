"""Gráficos do painel executivo — Plotly, paleta categórica fixa e validada.

Cores atribuídas por identidade da categoria (nunca por posição/ranking), para que
o mesmo tipo de fonte ou perspectiva mantenha sempre a mesma cor entre relatórios.
"""

from __future__ import annotations

from collections import Counter

import plotly.graph_objects as go
import streamlit as st

from radar.models import Evidence, PanelSection, SupportLevel

# Paleta categórica (8 tons, ordem fixa — nunca ciclada nem reordenada por ranking).
_CAT = ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7", "#e34948", "#e87ba4", "#eb6834"]
_BLUE = _CAT[0]  # hue único para gráficos de magnitude (não-categóricos)
_INK = "#0b0b0b"
_MUTED = "#898781"
_GRID = "#e1e0d9"
_SURFACE = "#fcfcfb"
_FONT = dict(family="Segoe UI, sans-serif", color=_INK, size=13)

_MIN_DATED_EVIDENCE = 5
_MIN_YEARS_FOR_TIMELINE = 2

_SOURCE_TYPE_META = {
    "scientific": ("Científica", _CAT[0]),
    "market": ("Mercado", _CAT[1]),
    "news": ("Notícias", _CAT[2]),
    "corporate": ("Corporativa", _CAT[3]),
    "patent": ("Patente", _CAT[4]),
}

_PERSPECTIVE_META = {
    "technical": ("Técnica", _CAT[0]),
    "economic": ("Econômica", _CAT[1]),
    "industrial": ("Industrial", _CAT[2]),
    "regulatory": ("Regulatória", _CAT[3]),
}

_SUPPORT_SCORE = {
    SupportLevel.INFERENCE: 0,
    SupportLevel.LOW: 1,
    SupportLevel.MEDIUM: 2,
    SupportLevel.HIGH: 3,
}

_SECTION_LABELS_SHORT = {
    "definition": "Definição",
    "maturity": "Maturidade",
    "applications": "Aplicações",
    "sectors": "Setores",
    "players": "Players",
    "investments": "Investimentos",
    "adoption_signals": "Adoção",
    "opportunities": "Oportunidades",
    "risks": "Riscos",
    "outlook": "Perspectivas",
}

_LANGUAGE_NAMES = {"pt": "Português", "en": "Inglês", "es": "Espanhol", "fr": "Francês"}
_LANGUAGE_COLORS = {"en": _CAT[0], "pt": _CAT[1], "es": _CAT[2], "fr": _CAT[3]}


def _base_layout(**overrides) -> dict:
    layout = dict(
        paper_bgcolor=_SURFACE,
        plot_bgcolor=_SURFACE,
        font=_FONT,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
    )
    layout.update(overrides)
    return layout


def _plot(fig: go.Figure, key: str) -> None:
    fig.update_layout(**_base_layout())
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False}, key=key)


def render_overview_charts(evidence: list[Evidence], sections: list[PanelSection]) -> None:
    if not evidence:
        return

    st.markdown("#### Visão geral em gráficos")
    st.caption(
        "Leitura visual do corpus de evidências e da robustez do painel — "
        "passe o mouse sobre cada marca para os valores exatos."
    )

    col1, col2 = st.columns(2)
    with col1:
        _render_source_type_mix(evidence)
    with col2:
        _render_perspective_distribution(evidence)

    _render_maturity_radar(sections)

    col3, col4 = st.columns(2)
    with col3:
        _render_top_origins(evidence)
    with col4:
        _render_timeline(evidence)

    _render_language_mix(evidence)


def _render_source_type_mix(evidence: list[Evidence]) -> None:
    st.markdown("**Mix por tipo de fonte**")
    counts = Counter(ev.source_type.value for ev in evidence)
    labels, colors, values = [], [], []
    for key, (label, color) in _SOURCE_TYPE_META.items():
        if counts.get(key):
            labels.append(label)
            colors.append(color)
            values.append(counts[key])

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color=_SURFACE, width=2)),
            hole=0.55,
            textinfo="label+percent",
            textfont=dict(color=_INK, size=12),
            hovertemplate="%{label}: %{value} evidência(s) (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(showlegend=True, legend=dict(orientation="h", y=-0.15)))
    _plot(fig, "chart-source-type")
    with st.expander("Ver dados"):
        rows = zip(labels, values, strict=True)
        st.table([{"Tipo de fonte": lbl, "Evidências": v} for lbl, v in rows])


def _render_perspective_distribution(evidence: list[Evidence]) -> None:
    st.markdown("**Evidência por perspectiva do agente coletor**")
    counts = Counter(ev.perspective for ev in evidence if ev.perspective in _PERSPECTIVE_META)
    if not counts:
        st.caption("Nenhuma evidência de mercado com perspectiva registrada nesta coleta.")
        return

    labels, colors, values = [], [], []
    for key, (label, color) in _PERSPECTIVE_META.items():
        labels.append(label)
        colors.append(color)
        values.append(counts.get(key, 0))

    fig = go.Figure(
        go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors),
            text=values,
            textposition="outside",
            hovertemplate="%{x}: %{y} evidência(s)<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            xaxis=dict(showgrid=False, linecolor=_GRID, tickfont=dict(color=_MUTED)),
            yaxis=dict(
                showgrid=True,
                gridcolor=_GRID,
                tickfont=dict(color=_MUTED),
                zeroline=False,
                range=[0, max(values) * 1.2],
            ),
        )
    )
    _plot(fig, "chart-perspective")
    st.caption(
        "4 agentes rodam em paralelo, cada um sob um ângulo diferente do mesmo tema "
        "(FR — Agente Coletor)."
    )


def _render_maturity_radar(sections: list[PanelSection]) -> None:
    st.markdown("**Radar de maturidade do relatório (nível de suporte por seção)**")
    labeled = [(s.key.value, s.support) for s in sections if s.support is not None]
    if len(labeled) < 3:
        st.caption("Seções insuficientes com grau de suporte calculado para o radar.")
        return

    categories = [_SECTION_LABELS_SHORT.get(key, key) for key, _ in labeled]
    scores = [_SUPPORT_SCORE[support.level] for _, support in labeled]
    # fecha o polígono
    categories_closed = categories + [categories[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure(
        go.Scatterpolar(
            r=scores_closed,
            theta=categories_closed,
            fill="toself",
            fillcolor="rgba(42,120,214,0.18)",
            line=dict(color=_BLUE, width=2),
            marker=dict(color=_BLUE, size=6),
            hovertemplate="%{theta}: %{r}/3<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            margin=dict(l=40, r=40, t=20, b=20),
            polar=dict(
                bgcolor=_SURFACE,
                radialaxis=dict(
                    range=[0, 3],
                    tickvals=[0, 1, 2, 3],
                    ticktext=["Inferência", "Baixo", "Médio", "Alto"],
                    gridcolor=_GRID,
                    linecolor=_GRID,
                    tickfont=dict(color=_MUTED, size=10),
                ),
                angularaxis=dict(
                    gridcolor=_GRID, linecolor=_GRID, tickfont=dict(color=_INK, size=11)
                ),
            ),
        )
    )
    _plot(fig, "chart-radar")
    with st.expander("Ver dados"):
        st.table(
            [
                {"Seção": cat, "Suporte": ["Inferência", "Baixo", "Médio", "Alto"][score]}
                for cat, score in zip(categories, scores, strict=True)
            ]
        )


def _render_top_origins(evidence: list[Evidence], top_n: int = 8) -> None:
    st.markdown("**Fontes/instituições mais citadas**")
    counts: Counter[str] = Counter()
    for ev in evidence:
        origin = ev.origin.removeprefix("Web Search: ")
        counts[origin] += 1
    top = counts.most_common(top_n)
    if not top:
        st.caption("Sem evidências para listar fontes.")
        return
    top.reverse()  # maior barra no topo
    labels = [o for o, _ in top]
    values = [c for _, c in top]

    fig = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker=dict(color=_BLUE),
            text=values,
            textposition="outside",
            hovertemplate="%{y}: %{x} evidência(s)<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            margin=dict(l=10, r=30, t=10, b=10),
            xaxis=dict(
                showgrid=True,
                gridcolor=_GRID,
                tickfont=dict(color=_MUTED),
                zeroline=False,
                range=[0, max(values) * 1.2],
            ),
            yaxis=dict(showgrid=False, tickfont=dict(color=_INK, size=11)),
        )
    )
    _plot(fig, "chart-origins")


def _render_timeline(evidence: list[Evidence]) -> None:
    st.markdown("**Publicações por ano**")
    dated = [ev for ev in evidence if ev.published_at is not None]
    years = Counter(ev.published_at.year for ev in dated)

    if len(dated) < _MIN_DATED_EVIDENCE or len(years) < _MIN_YEARS_FOR_TIMELINE:
        st.caption(
            f"Apenas {len(dated)} de {len(evidence)} evidências têm data de publicação "
            "nesta coleta — sinal insuficiente para uma linha do tempo confiável."
        )
        return

    ordered_years = sorted(years)
    values = [years[y] for y in ordered_years]

    fig = go.Figure(
        go.Scatter(
            x=ordered_years,
            y=values,
            mode="lines+markers",
            line=dict(color=_BLUE, width=2),
            marker=dict(color=_BLUE, size=8),
            fill="tozeroy",
            fillcolor="rgba(42,120,214,0.12)",
            hovertemplate="%{x}: %{y} evidência(s)<extra></extra>",
        )
    )
    fig.update_layout(
        **_base_layout(
            xaxis=dict(showgrid=False, linecolor=_GRID, tickfont=dict(color=_MUTED), dtick=1),
            yaxis=dict(
                showgrid=True,
                gridcolor=_GRID,
                tickfont=dict(color=_MUTED),
                zeroline=False,
                rangemode="tozero",
            ),
        )
    )
    _plot(fig, "chart-timeline")


def _render_language_mix(evidence: list[Evidence]) -> None:
    counts = Counter(ev.language for ev in evidence)
    if len(counts) < 2:
        lang = next(iter(counts), None)
        if lang:
            name = _LANGUAGE_NAMES.get(lang, lang.upper())
            st.caption(f"🌐 100% das fontes desta coleta estão em {name}.")
        return

    st.markdown("**Idioma das fontes**")
    ordered = counts.most_common()
    # cores por idioma (identidade fixa) — códigos fora do dicionário caem no fim
    # da paleta, em ordem alfabética estável, nunca por frequência nesta coleta.
    unknown_langs = sorted({lang for lang, _ in ordered if lang not in _LANGUAGE_COLORS})
    fallback_colors = iter(c for c in _CAT if c not in _LANGUAGE_COLORS.values())
    unknown_color_map = dict(zip(unknown_langs, fallback_colors, strict=False))

    labels = [_LANGUAGE_NAMES.get(lang, lang.upper()) for lang, _ in ordered]
    values = [v for _, v in ordered]
    colors = [
        _LANGUAGE_COLORS.get(lang, unknown_color_map.get(lang, _MUTED)) for lang, _ in ordered
    ]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors, line=dict(color=_SURFACE, width=2)),
            hole=0.55,
            textinfo="label+percent",
            textfont=dict(color=_INK, size=12),
            hovertemplate="%{label}: %{value} evidência(s) (%{percent})<extra></extra>",
        )
    )
    fig.update_layout(**_base_layout(showlegend=True, legend=dict(orientation="h", y=-0.15)))
    _plot(fig, "chart-language")
