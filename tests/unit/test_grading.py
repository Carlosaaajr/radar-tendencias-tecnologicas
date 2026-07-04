from radar.models import Evidence, PanelSection, SectionKey, SourceType, SupportLevel
from radar.synthesis.grading import grade_report, grade_section


def _ev(id_: str, source_type: SourceType) -> Evidence:
    return Evidence(
        id=id_,
        title=f"Title {id_}",
        source_type=source_type,
        origin="origin",
        url=f"https://example.com/{id_}",
        snippet="snippet",
        language="en",
    )


def _corpus(*pairs: tuple[str, SourceType]) -> dict[str, Evidence]:
    return {id_: _ev(id_, st) for id_, st in pairs}


def _section(evidence_ids: list[str], is_inference: bool = False, divergence: str | None = None) -> PanelSection:
    return PanelSection(
        key=SectionKey.DEFINITION,
        content_md="texto",
        evidence_ids=evidence_ids,
        is_inference=is_inference,
        divergence_note=divergence,
    )


def test_inference_zero_evidence():
    section = _section([], is_inference=True)
    grade = grade_section(section, {})
    assert grade.evidence_count == 0
    assert grade.level == SupportLevel.INFERENCE


def test_low_one_evidence():
    corpus = _corpus(("ev-1", SourceType.NEWS))
    section = _section(["ev-1"])
    grade = grade_section(section, corpus)
    assert grade.evidence_count == 1
    assert grade.level == SupportLevel.LOW


def test_medium_two_to_three_evidence():
    corpus = _corpus(("ev-1", SourceType.NEWS), ("ev-2", SourceType.MARKET))
    section = _section(["ev-1", "ev-2"])
    grade = grade_section(section, corpus)
    assert grade.evidence_count == 2
    assert grade.level == SupportLevel.MEDIUM


def test_medium_four_evidence_but_single_type_not_high():
    """Regra totalizada (R8): >=4 evidencias com <2 tipos cai em medium, nao high."""
    corpus = _corpus(
        ("ev-1", SourceType.NEWS),
        ("ev-2", SourceType.NEWS),
        ("ev-3", SourceType.NEWS),
        ("ev-4", SourceType.NEWS),
    )
    section = _section(["ev-1", "ev-2", "ev-3", "ev-4"])
    grade = grade_section(section, corpus)
    assert grade.evidence_count == 4
    assert grade.source_type_count == 1
    assert grade.level == SupportLevel.MEDIUM


def test_high_four_evidence_two_types():
    corpus = _corpus(
        ("ev-1", SourceType.NEWS),
        ("ev-2", SourceType.MARKET),
        ("ev-3", SourceType.SCIENTIFIC),
        ("ev-4", SourceType.CORPORATE),
    )
    section = _section(["ev-1", "ev-2", "ev-3", "ev-4"])
    grade = grade_section(section, corpus)
    assert grade.evidence_count == 4
    assert grade.source_type_count == 4
    assert grade.level == SupportLevel.HIGH


def test_divergence_flag_mirrors_divergence_note():
    corpus = _corpus(("ev-1", SourceType.NEWS), ("ev-2", SourceType.MARKET))
    section = _section(["ev-1", "ev-2"], divergence="fontes discordam")
    grade = grade_section(section, corpus)
    assert grade.has_divergence is True


def test_grade_report_fills_support_for_all_sections():
    corpus = _corpus(("ev-1", SourceType.NEWS), ("ev-2", SourceType.MARKET))
    sections = [_section(["ev-1", "ev-2"]), _section([], is_inference=True)]
    graded = grade_report(sections, corpus)
    assert all(s.support is not None for s in graded)
    assert graded[0].support.level == SupportLevel.MEDIUM
    assert graded[1].support.level == SupportLevel.INFERENCE
