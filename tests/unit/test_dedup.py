from radar.models import Evidence, SourceType
from radar.synthesis.dedup import dedup_evidence


def _ev(**overrides) -> Evidence:
    defaults = dict(
        id="ev-1",
        title="Edge AI adoption in manufacturing",
        source_type=SourceType.NEWS,
        origin="TechCrunch",
        url="https://example.com/article",
        snippet="Some snippet.",
        language="en",
    )
    defaults.update(overrides)
    return Evidence(**defaults)


def test_no_duplicates_returns_all():
    items = [
        _ev(id="ev-1", title="Edge AI adoption in manufacturing", url="https://a.com/1"),
        _ev(id="ev-2", title="Quantum Computing Breakthroughs", url="https://b.com/2"),
    ]
    result = dedup_evidence(items)
    assert len(result) == 2


def test_duplicate_url_with_tracking_params_removed():
    items = [
        _ev(id="ev-1", url="https://example.com/article?utm_source=twitter&utm_medium=social"),
        _ev(id="ev-2", url="https://example.com/article"),
    ]
    result = dedup_evidence(items)
    assert len(result) == 1


def test_duplicate_url_trailing_slash_and_case_insensitive_host():
    items = [
        _ev(id="ev-1", url="https://Example.COM/article/"),
        _ev(id="ev-2", url="https://example.com/article"),
    ]
    result = dedup_evidence(items)
    assert len(result) == 1


def test_similar_title_different_url_deduplicated():
    items = [
        _ev(id="ev-1", title="Edge AI Adoption In Manufacturing!", url="https://site-a.com/x"),
        _ev(id="ev-2", title="edge ai adoption in manufacturing", url="https://site-b.com/y"),
    ]
    result = dedup_evidence(items)
    assert len(result) == 1


def test_dissimilar_titles_not_deduplicated():
    items = [
        _ev(id="ev-1", title="Edge AI Adoption In Manufacturing", url="https://site-a.com/x"),
        _ev(id="ev-2", title="Quantum Computing Breakthroughs", url="https://site-b.com/y"),
    ]
    result = dedup_evidence(items)
    assert len(result) == 2


def test_dedup_keeps_richer_metadata():
    poor = _ev(id="ev-1", url="https://example.com/article", citation_count=None, published_at=None)
    rich = _ev(id="ev-2", url="https://example.com/article", citation_count=10, published_at="2026-01-01")

    result = dedup_evidence([poor, rich])
    assert len(result) == 1
    kept = result[0]
    assert kept.citation_count == 10
    assert kept.published_at is not None
