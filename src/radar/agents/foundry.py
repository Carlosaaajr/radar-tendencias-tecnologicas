"""Cliente Foundry compartilhado — nova agents API, Web Search tool nativo (R1).

Validado pelo spike T006 (infra/spike_web_search.py): a Responses API é stateless por
chamada (model + tools + input) — não há um recurso "Agent" persistente a criar/reusar
no servidor, ao contrário do que a Assistants API "classic" exigia.
"""

from __future__ import annotations

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from radar.config import get_settings

_client: AIProjectClient | None = None
_openai_client = None


def get_openai_client():
    global _client, _openai_client
    if _openai_client is not None:
        return _openai_client

    settings = get_settings()
    _client = AIProjectClient(
        endpoint=settings.project_endpoint,
        credential=DefaultAzureCredential(),
    )
    _openai_client = _client.get_openai_client()
    return _openai_client
