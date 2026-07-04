"""arXiv API collector (Atom feed) — R3."""

from __future__ import annotations

import feedparser
import httpx

from radar.collectors.base import CollectorResult
from radar.models import SNIPPET_MAX_LENGTH, Evidence, SourceType

ARXIV_API_URL = "http://export.arxiv.org/api/query"


class ArxivCollector:
    name = "arxiv"
    source_type = SourceType.SCIENTIFIC

    async def collect(
        self, theme: str, *, limit: int = 10, timeout_s: float = 30
    ) -> CollectorResult:
        params = {
            "search_query": f"all:{theme}",
            "max_results": limit,
        }
        try:
            async with httpx.AsyncClient(timeout=timeout_s) as client:
                response = await client.get(ARXIV_API_URL, params=params)
                response.raise_for_status()
        except (httpx.TimeoutException, httpx.HTTPError) as exc:
            return CollectorResult(evidence=[], degraded=True, error=str(exc))

        feed = feedparser.parse(response.text)
        evidence: list[Evidence] = []
        for entry in feed.entries:
            url = getattr(entry, "id", None) or getattr(entry, "link", None)
            if not url:
                continue
            published = None
            if getattr(entry, "published", None):
                published = entry.published[:10]
            evidence.append(
                Evidence(
                    id=f"ev-{len(evidence) + 1}",
                    title=entry.get("title", "").strip(),
                    source_type=SourceType.SCIENTIFIC,
                    origin="arXiv",
                    url=url,
                    published_at=published,
                    snippet=entry.get("summary", "").strip()[:SNIPPET_MAX_LENGTH],
                    language="en",
                )
            )
        return CollectorResult(evidence=evidence, degraded=False, error=None)
