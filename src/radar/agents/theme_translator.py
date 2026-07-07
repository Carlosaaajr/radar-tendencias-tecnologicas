"""Tradutor de tema para inglês — usado apenas antes de consultar arXiv/OpenAlex.

Achado real (avaliação crítica, 2026-07-07): essas duas bases são predominantemente
em inglês; um tema em português com palavras curtas e comuns ("por", "IA") produz
matches espúrios por substring/stem contra títulos não relacionados (ex.: "por" casando
com "PoR" de "Proof of Reference"). A qualificação industrial determinística
(industrial_scope.py) sozinha não resolve isso — o problema é a língua do texto-base
da busca, não só a falta de recorte de domínio. Esta chamada é única, sem ferramentas
(sem Web Search), curta e barata — não confundir com a coleta em si.
"""

from __future__ import annotations

import asyncio

from radar.agents.foundry import get_openai_client
from radar.config import get_settings

_TRANSLATE_PROMPT = """Translate the following technology/industry trend theme to \
English. If it is already in English, return it unchanged. Preserve proper nouns, \
acronyms and technical terms as-is.

Respond with ONLY the translated (or unchanged) theme text — no quotes, no \
explanation, no extra words.

Theme: "{theme}"
"""


class TranslationError(Exception):
    """Falha ao traduzir o tema (rede/API) — o chamador MUST tratar como fail-open
    (Princípio IV), usando o tema original em português."""


async def translate_theme_to_english(theme: str, *, timeout_s: float = 15) -> str:
    settings = get_settings()
    client = get_openai_client()
    try:
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.model_deployment_name,
            input=_TRANSLATE_PROMPT.format(theme=theme),
            timeout=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 — erro de API vira TranslationError tipado
        raise TranslationError(str(exc)) from exc

    translated = (getattr(response, "output_text", "") or "").strip()
    if not translated:
        raise TranslationError("Tradução vazia retornada pelo modelo")
    return translated
