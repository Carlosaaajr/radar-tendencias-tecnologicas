"""Deduplicação de evidências (contracts §5, FR-007) — puro e determinístico."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from urllib.parse import urlsplit, urlunsplit

from radar.models import Evidence

TITLE_SIMILARITY_THRESHOLD = 0.9
_TRACKING_PARAM_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")


def _normalize_url(url: str) -> str:
    parts = urlsplit(str(url))
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/")
    query_pairs = [
        kv
        for kv in parts.query.split("&")
        if kv and not kv.split("=")[0].lower().startswith(_TRACKING_PARAM_PREFIXES)
    ]
    query = "&".join(sorted(query_pairs))
    return urlunsplit((scheme, netloc, path, query, ""))


def _normalize_title(title: str) -> str:
    no_punct = re.sub(r"[^\w\s]", "", title)
    return " ".join(no_punct.casefold().split())


def _richness_score(evidence: Evidence) -> int:
    score = 0
    if evidence.citation_count is not None:
        score += 1
    if evidence.published_at is not None:
        score += 1
    score += len(evidence.snippet)
    return score


def dedup_evidence(items: list[Evidence]) -> list[Evidence]:
    kept: list[Evidence] = []
    kept_urls: list[str] = []
    kept_titles: list[str] = []

    for item in items:
        norm_url = _normalize_url(str(item.url))
        norm_title = _normalize_title(item.title)

        match_index = None
        pairs = enumerate(zip(kept_urls, kept_titles, strict=True))
        for i, (existing_url, existing_title) in pairs:
            if norm_url == existing_url:
                match_index = i
                break
            ratio = SequenceMatcher(None, norm_title, existing_title).ratio()
            if ratio >= TITLE_SIMILARITY_THRESHOLD:
                match_index = i
                break

        if match_index is None:
            kept.append(item)
            kept_urls.append(norm_url)
            kept_titles.append(norm_title)
        elif _richness_score(item) > _richness_score(kept[match_index]):
            kept[match_index] = item
            kept_urls[match_index] = norm_url
            kept_titles[match_index] = norm_title

    return kept
