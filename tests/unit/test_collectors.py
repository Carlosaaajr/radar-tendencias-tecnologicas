from pathlib import Path

import httpx
import pytest
import respx

from radar.collectors.arxiv import ARXIV_API_URL, ArxivCollector
from radar.collectors.openalex import OPENALEX_API_URL, OpenAlexCollector
from radar.models import SourceType

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.mark.asyncio
@respx.mock
async def test_arxiv_collector_parses_atom_fixture():
    body = (FIXTURES / "arxiv_atom.xml").read_text(encoding="utf-8")
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=body))

    collector = ArxivCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=5)

    assert result.degraded is False
    assert result.error is None
    assert len(result.evidence) == 2
    assert all(e.source_type == SourceType.SCIENTIFIC for e in result.evidence)
    assert all(str(e.url).startswith("http://arxiv.org/abs/") for e in result.evidence)
    titles = {e.title for e in result.evidence}
    assert "Edge AI Inference Optimization for Industrial IoT Devices" in titles


@pytest.mark.asyncio
@respx.mock
async def test_arxiv_collector_timeout_returns_degraded_no_exception():
    respx.get(ARXIV_API_URL).mock(side_effect=httpx.TimeoutException("timed out"))

    collector = ArxivCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=1)

    assert result.degraded is True
    assert result.error is not None
    assert result.evidence == []


@pytest.mark.asyncio
@respx.mock
async def test_openalex_collector_parses_json_fixture():
    import json

    body = json.loads((FIXTURES / "openalex_response.json").read_text(encoding="utf-8"))
    respx.get(OPENALEX_API_URL).mock(return_value=httpx.Response(200, json=body))

    collector = OpenAlexCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=5)

    assert result.degraded is False
    assert len(result.evidence) == 2
    assert all(e.source_type == SourceType.SCIENTIFIC for e in result.evidence)
    citation_counts = {e.citation_count for e in result.evidence}
    assert citation_counts == {15, 42}


@pytest.mark.asyncio
@respx.mock
async def test_openalex_collector_server_error_returns_degraded():
    respx.get(OPENALEX_API_URL).mock(return_value=httpx.Response(500))

    collector = OpenAlexCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=5)

    assert result.degraded is True
    assert result.evidence == []


@pytest.mark.asyncio
@respx.mock
async def test_evidence_without_url_is_discarded():
    import json

    fixture = json.loads((FIXTURES / "openalex_response.json").read_text(encoding="utf-8"))
    fixture["results"][0]["primary_location"] = None
    fixture["results"][0]["doi"] = None
    respx.get(OPENALEX_API_URL).mock(return_value=httpx.Response(200, json=fixture))

    collector = OpenAlexCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=5)

    # o item sem URL utilizável eh descartado; o outro item permanece
    assert len(result.evidence) == 1


@pytest.mark.asyncio
@respx.mock
async def test_openalex_null_source_does_not_crash_collection():
    """Regressao: work com primary_location.source=null (comum em preprints) nao
    pode derrubar a coleta inteira (achado H1 da revisao de codigo)."""
    import json

    fixture = json.loads((FIXTURES / "openalex_response.json").read_text(encoding="utf-8"))
    fixture["results"][0]["primary_location"]["source"] = None
    respx.get(OPENALEX_API_URL).mock(return_value=httpx.Response(200, json=fixture))

    collector = OpenAlexCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=5)

    assert result.degraded is False
    assert len(result.evidence) == 2
    first = next(e for e in result.evidence if e.id == "ev-1")
    assert first.origin == "OpenAlex"


@pytest.mark.asyncio
@respx.mock
async def test_arxiv_query_gains_industrial_qualifier_when_theme_unscoped():
    body = (FIXTURES / "arxiv_atom.xml").read_text(encoding="utf-8")
    route = respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=body))

    await ArxivCollector().collect("IoT", limit=10, timeout_s=5)

    sent_query = route.calls[0].request.url.params["search_query"]
    assert sent_query.startswith("all:IoT AND (")
    assert 'all:"industrial"' in sent_query


@pytest.mark.asyncio
@respx.mock
async def test_arxiv_query_unchanged_when_theme_already_industrial():
    body = (FIXTURES / "arxiv_atom.xml").read_text(encoding="utf-8")
    route = respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=body))

    await ArxivCollector().collect("IoT industrial", limit=10, timeout_s=5)

    sent_query = route.calls[0].request.url.params["search_query"]
    assert sent_query == "all:IoT industrial"


@pytest.mark.asyncio
@respx.mock
async def test_openalex_query_gains_industrial_qualifier_when_theme_unscoped():
    import json

    body = json.loads((FIXTURES / "openalex_response.json").read_text(encoding="utf-8"))
    route = respx.get(OPENALEX_API_URL).mock(return_value=httpx.Response(200, json=body))

    await OpenAlexCollector().collect("IoT", limit=10, timeout_s=5)

    sent_query = route.calls[0].request.url.params["search"]
    assert sent_query.startswith("IoT AND (")
    assert '"industrial"' in sent_query


@pytest.mark.asyncio
@respx.mock
async def test_openalex_query_unchanged_when_theme_already_industrial():
    import json

    body = json.loads((FIXTURES / "openalex_response.json").read_text(encoding="utf-8"))
    route = respx.get(OPENALEX_API_URL).mock(return_value=httpx.Response(200, json=body))

    await OpenAlexCollector().collect("IoT industrial", limit=10, timeout_s=5)

    sent_query = route.calls[0].request.url.params["search"]
    assert sent_query == "IoT industrial"


@pytest.mark.asyncio
@respx.mock
async def test_snippet_truncated_to_500_chars():
    body = (FIXTURES / "arxiv_atom.xml").read_text(encoding="utf-8")
    long_summary = "x" * 1000
    body = body.replace(
        "We propose a lightweight quantization scheme for running deep neural\n"
        "networks on resource-constrained edge devices in industrial settings, reducing\n"
        "latency by 40% without significant accuracy loss.",
        long_summary,
    )
    respx.get(ARXIV_API_URL).mock(return_value=httpx.Response(200, text=body))

    collector = ArxivCollector()
    result = await collector.collect("Edge AI", limit=10, timeout_s=5)

    assert all(len(e.snippet) <= 500 for e in result.evidence)
