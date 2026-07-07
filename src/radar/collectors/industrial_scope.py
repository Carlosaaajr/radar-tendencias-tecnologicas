"""Refinamento determinístico de query — mitiga temas sem recorte de aplicação
(ex.: "IoT" em vez de "IoT industrial"), que fazem os coletores acadêmicos
(busca literal por palavra-chave) devolverem evidência sem correlação com o
ambiente industrial, derrubando o grau de suporte de um tema tecnicamente
válido. Ver achado em docs/critical-review.md.
"""

from __future__ import annotations

_INDUSTRIAL_HINTS = (
    "industrial",
    "indústria",
    "industria",
    "manufacturing",
    "manufatura",
    "factory",
    "fábrica",
    "fabrica",
    "industry 4.0",
    "indústria 4.0",
    "industria 4.0",
    "production line",
    "linha de produção",
    "linha de producao",
    "shop floor",
    "chão de fábrica",
    "chao de fabrica",
)

INDUSTRIAL_QUALIFIER_TERMS = ("industrial", "manufacturing", "industry 4.0")


def needs_industrial_scoping(theme: str) -> bool:
    """True quando o tema não menciona explicitamente um recorte industrial —
    sinal de que a busca literal nos coletores acadêmicos pode trazer evidência
    fora do ambiente industrial (ex.: "IoT" sem qualificação)."""
    theme_lower = theme.lower()
    return not any(hint in theme_lower for hint in _INDUSTRIAL_HINTS)
