"""Guardrail de escopo — valida que o tema é uma tendência/tecnologia/conceito
industrial antes de rodar o pipeline caro (coleta + síntese).

Achado real (avaliação crítica): nenhuma validação de escopo existia — qualquer texto
livre disparava o pipeline completo (arXiv + OpenAlex + 4 buscas do Agente Coletor +
síntese), com custo real mesmo para temas fora de contexto. Esta chamada é única, sem
ferramentas (sem Web Search), curta e barata — não confundir com a coleta em si.
"""

from __future__ import annotations

import asyncio

from radar.agents.foundry import get_openai_client
from radar.config import get_settings

_SCOPE_PROMPT = """Você é um classificador de escopo para uma plataforma de radar de \
tendências tecnológicas industriais.

O texto a seguir descreve uma tendência, tecnologia ou conceito tecnológico/industrial \
válido para gerar uma análise de mercado? Exemplos válidos: "Edge AI", "Robôs \
Humanoides para Indústria", "Impressão 3D metálica", "Digital twins", "Hidrogênio \
verde". Exemplos inválidos: perguntas genéricas, pedidos não relacionados a tecnologia \
industrial, texto vazio ou sem sentido.

Responda com exatamente uma palavra, sem explicação: SIM ou NAO.

Texto: "{theme}"
"""


class ScopeCheckError(Exception):
    """Falha ao consultar o classificador de escopo (rede/API) — nunca deve bloquear
    uma análise legítima; o chamador MUST tratar como fail-open (Princípio IV)."""


async def is_in_scope(theme: str, *, timeout_s: float = 20) -> bool:
    settings = get_settings()
    client = get_openai_client()
    try:
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.model_deployment_name,
            input=_SCOPE_PROMPT.format(theme=theme),
            timeout=timeout_s,
        )
    except Exception as exc:  # noqa: BLE001 — erro de API vira ScopeCheckError tipado
        raise ScopeCheckError(str(exc)) from exc

    answer = (getattr(response, "output_text", "") or "").strip().upper()
    return answer.startswith("SIM")
