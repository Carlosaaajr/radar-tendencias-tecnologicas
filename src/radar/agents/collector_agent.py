"""Agente Coletor — perguntas multi-perspectiva (R2) + Web Search tool nativo (R1).

Confirmado pelo spike T006: `responses.create(model=..., tools=[{"type": "web_search"}])`
devolve item.type="message" com annotations tipo "url_citation" contendo
{url, title, start_index, end_index}. As 4 perguntas MUST rodar concorrentes
(asyncio.gather) — sequencial (30s/pergunta medido no spike) estoura SC-001.
"""

from __future__ import annotations

import asyncio
import re
from urllib.parse import urlsplit

from radar.agents.foundry import get_openai_client
from radar.collectors.base import CollectorResult
from radar.config import get_settings
from radar.models import SNIPPET_MAX_LENGTH, Evidence, SourceType

PERSPECTIVES = ("technical", "economic", "industrial", "regulatory")

_PERSPECTIVE_PROMPTS = {
    "technical": "What are the key technical characteristics, architecture and "
    "maturity level of {theme}? Search the web and cite sources with URLs.",
    "economic": "What investments, market size and market movements are happening "
    "around {theme}? Search the web and cite sources with URLs.",
    "industrial": "What industrial sectors, companies and adoption signals exist for "
    "{theme}? Search the web and cite sources with URLs.",
    "regulatory": "What regulatory developments, risks and challenges are associated "
    "with {theme}, including patent activity? Search the web and cite sources with URLs.",
}

_NEWS_DOMAINS = ("techcrunch", "reuters", "bloomberg", "wired", "theverge", "technologyreview")
_CORPORATE_DOMAINS = (
    "nvidia.com", "siemens.com", "intel.com", "microsoft.com", "google.com",
    "accenture.com", "ibm.com",
)
_MARKET_DOMAINS = ("gartner.com", "mckinsey.com", "deloitte.com", "weforum.org", "oecd.org")
_PATENT_DOMAINS = ("patents.google.com", "epo.org", "uspto.gov")


def _infer_source_type(url: str) -> SourceType:
    host = urlsplit(url).netloc.lower()
    if any(d in host for d in _PATENT_DOMAINS):
        return SourceType.PATENT
    if any(d in host for d in _MARKET_DOMAINS):
        return SourceType.MARKET
    if any(d in host for d in _CORPORATE_DOMAINS):
        return SourceType.CORPORATE
    if any(d in host for d in _NEWS_DOMAINS):
        return SourceType.NEWS
    return SourceType.NEWS


async def _ask_perspective(theme: str, perspective: str, timeout_s: float) -> list[Evidence]:
    settings = get_settings()
    client = get_openai_client()
    question = _PERSPECTIVE_PROMPTS[perspective].format(theme=theme)

    response = await asyncio.to_thread(
        client.responses.create,
        model=settings.model_deployment_name,
        input=question,
        tools=[{"type": "web_search"}],
        timeout=timeout_s,
    )

    evidence: list[Evidence] = []
    seen_urls: set[str] = set()
    for item in response.output:
        if getattr(item, "type", None) != "message":
            continue
        for content_item in getattr(item, "content", None) or []:
            text = getattr(content_item, "text", "") or ""
            for ann in getattr(content_item, "annotations", None) or []:
                if getattr(ann, "type", None) != "url_citation":
                    continue
                url = getattr(ann, "url", None)
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                start = getattr(ann, "start_index", None)
                end = getattr(ann, "end_index", None)
                snippet = text[start:end] if start is not None and end is not None else ""
                snippet = re.sub(r"\s+", " ", snippet).strip()[:SNIPPET_MAX_LENGTH]
                evidence.append(
                    Evidence(
                        id=f"ev-{len(evidence) + 1}",
                        title=getattr(ann, "title", None) or url,
                        source_type=_infer_source_type(url),
                        origin=f"Web Search: {urlsplit(url).netloc}",
                        url=url,
                        snippet=snippet,
                        language="en",
                        perspective=perspective,
                    )
                )
    return evidence


async def run_market_collection(
    theme: str, *, perspectives: tuple[str, ...] = PERSPECTIVES, timeout_s: float = 60
) -> CollectorResult:
    try:
        results = await asyncio.gather(
            *(_ask_perspective(theme, p, timeout_s) for p in perspectives),
            return_exceptions=True,
        )
    except Exception as exc:  # noqa: BLE001 — degradação nunca propaga (FR-012)
        return CollectorResult(evidence=[], degraded=True, error=str(exc))

    evidence: list[Evidence] = []
    errors: list[str] = []
    for perspective, result in zip(perspectives, results, strict=True):
        if isinstance(result, Exception):
            errors.append(f"{perspective}: {result}")
            continue
        evidence.extend(result)

    if not evidence and errors:
        return CollectorResult(evidence=[], degraded=True, error="; ".join(errors))

    for i, ev in enumerate(evidence, start=1):
        ev.id = f"ev-{i}"

    return CollectorResult(
        evidence=evidence,
        degraded=bool(errors),
        error="; ".join(errors) if errors else None,
    )
