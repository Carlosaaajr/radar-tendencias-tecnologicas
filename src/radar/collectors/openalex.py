"""OpenAlex API collector (JSON) — R3."""

from __future__ import annotations

import httpx

from radar.collectors.base import CollectorResult
from radar.config import get_settings
from radar.models import SNIPPET_MAX_LENGTH, Evidence, SourceType

OPENALEX_API_URL = "https://api.openalex.org/works"


def _reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inverted_index.items():
        for i in idxs:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


class OpenAlexCollector:
    name = "openalex"
    source_type = SourceType.SCIENTIFIC

    async def collect(
        self, theme: str, *, limit: int = 10, timeout_s: float = 30
    ) -> CollectorResult:
        settings = get_settings()
        params: dict[str, str | int] = {"search": theme, "per_page": limit}
        if settings.openalex_mailto:
            params["mailto"] = settings.openalex_mailto

        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                response = await client.get(OPENALEX_API_URL, params=params)
                response.raise_for_status()
                data = response.json()

            evidence: list[Evidence] = []
            for work in data.get("results", []):
                primary = work.get("primary_location") or {}
                url = primary.get("landing_page_url") or work.get("doi")
                if not url:
                    continue
                title = (work.get("title") or "").strip()
                if not title:
                    continue
                source = primary.get("source") or {}
                origin = source.get("display_name") or "OpenAlex"
                snippet = _reconstruct_abstract(work.get("abstract_inverted_index"))
                evidence.append(
                    Evidence(
                        id=f"ev-{len(evidence) + 1}",
                        title=title,
                        source_type=SourceType.SCIENTIFIC,
                        origin=origin,
                        url=url,
                        published_at=work.get("publication_date"),
                        snippet=snippet[:SNIPPET_MAX_LENGTH],
                        language=work.get("language") or "en",
                        citation_count=work.get("cited_by_count"),
                    )
                )
        except (httpx.TimeoutException, httpx.HTTPError, ValueError) as exc:
            return CollectorResult(evidence=[], degraded=True, error=str(exc))
        except Exception as exc:  # noqa: BLE001 — registro malformado nunca derruba a coleta (FR-012)
            return CollectorResult(evidence=[], degraded=True, error=str(exc))

        return CollectorResult(evidence=evidence, degraded=False, error=None)
