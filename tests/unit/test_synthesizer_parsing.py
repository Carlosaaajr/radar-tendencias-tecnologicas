import json
from pathlib import Path

import pytest

from radar.agents.synthesizer_agent import SynthesisError, parse_synthesis_output
from radar.models import Evidence, SourceType

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _load_fixture(key: str) -> dict:
    data = json.loads((FIXTURES / "synthesizer_output.json").read_text(encoding="utf-8"))
    return data[key]


def _corpus() -> dict[str, Evidence]:
    ids = ["ev-1", "ev-2", "ev-3", "ev-4", "ev-5"]
    return {
        id_: Evidence(
            id=id_,
            title=f"Title {id_}",
            source_type=SourceType.NEWS,
            origin="origin",
            url=f"https://example.com/{id_}",
            snippet="snippet",
            language="en",
        )
        for id_ in ids
    }


def test_valid_output_parses_all_sections():
    raw = _load_fixture("valid")
    corpus = _corpus()

    result = parse_synthesis_output(raw, corpus)

    assert len(result.sections) == 4
    definition = next(s for s in result.sections if s.key == "definition")
    assert definition.is_inference is False
    assert definition.evidence_ids == ["ev-1", "ev-3"]


def test_valid_output_preserves_divergence_note():
    raw = _load_fixture("valid")
    corpus = _corpus()

    result = parse_synthesis_output(raw, corpus)

    risks = next(s for s in result.sections if s.key == "risks")
    assert risks.divergence_note is not None
    assert "diretrizes restritivas" in risks.divergence_note


def test_valid_output_inference_section_has_no_evidence_required():
    raw = _load_fixture("valid")
    corpus = _corpus()

    result = parse_synthesis_output(raw, corpus)

    outlook = next(s for s in result.sections if s.key == "outlook")
    assert outlook.is_inference is True
    assert outlook.evidence_ids == []


def test_orphan_evidence_id_downgrades_to_inference_with_warning():
    raw = _load_fixture("invalid_orphan_evidence_id")
    corpus = _corpus()

    result = parse_synthesis_output(raw, corpus)

    section = result.sections[0]
    assert section.is_inference is True
    assert any("ev-999" in w for w in result.raw_warnings)


def test_missing_required_field_raises_synthesis_error():
    raw = _load_fixture("invalid_missing_required_field")
    corpus = _corpus()

    with pytest.raises(SynthesisError):
        parse_synthesis_output(raw, corpus)


def test_bad_enum_key_raises_synthesis_error():
    raw = _load_fixture("invalid_bad_enum_key")
    corpus = _corpus()

    with pytest.raises(SynthesisError):
        parse_synthesis_output(raw, corpus)
