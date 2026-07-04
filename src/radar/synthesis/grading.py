"""Grau de suporte determinístico (contracts §4, R8) — puro, nunca vem do LLM."""

from __future__ import annotations

from radar.models import Evidence, PanelSection, SupportGrade, SupportLevel


def _level_for(evidence_count: int, source_type_count: int) -> SupportLevel:
    if evidence_count == 0:
        return SupportLevel.INFERENCE
    if evidence_count == 1:
        return SupportLevel.LOW
    if evidence_count >= 4 and source_type_count >= 2:
        return SupportLevel.HIGH
    return SupportLevel.MEDIUM


def grade_section(section: PanelSection, corpus: dict[str, Evidence]) -> SupportGrade:
    cited = [corpus[eid] for eid in section.evidence_ids if eid in corpus]
    evidence_count = len(cited)
    source_type_count = len({e.source_type for e in cited})
    level = _level_for(evidence_count, source_type_count)
    return SupportGrade(
        evidence_count=evidence_count,
        source_type_count=source_type_count,
        level=level,
        has_divergence=section.divergence_note is not None,
    )


def grade_report(
    sections: list[PanelSection], corpus: dict[str, Evidence]
) -> list[PanelSection]:
    graded = []
    for section in sections:
        grade = grade_section(section, corpus)
        graded.append(section.model_copy(update={"support": grade}))
    return graded
