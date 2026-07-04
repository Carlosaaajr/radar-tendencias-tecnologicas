"""Pydantic models for the Radar de Tendências pipeline (see data-model.md)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

SNIPPET_MAX_LENGTH = 500


class SourceType(StrEnum):
    SCIENTIFIC = "scientific"
    MARKET = "market"
    NEWS = "news"
    CORPORATE = "corporate"
    PATENT = "patent"


class SectionKey(StrEnum):
    DEFINITION = "definition"
    MATURITY = "maturity"
    APPLICATIONS = "applications"
    SECTORS = "sectors"
    PLAYERS = "players"
    INVESTMENTS = "investments"
    ADOPTION_SIGNALS = "adoption_signals"
    OPPORTUNITIES = "opportunities"
    RISKS = "risks"
    OUTLOOK = "outlook"


ALL_SECTION_KEYS: tuple[SectionKey, ...] = tuple(SectionKey)


class ReportStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"


class SupportLevel(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFERENCE = "inference"


class Evidence(BaseModel):
    id: str = Field(pattern=r"^ev-\d+$")
    title: str = Field(min_length=1)
    source_type: SourceType
    origin: str
    url: HttpUrl
    published_at: date | None = None
    snippet: str = ""
    language: str = Field(min_length=2, max_length=5)
    perspective: str | None = None
    citation_count: int | None = Field(default=None, ge=0)

    @field_validator("snippet")
    @classmethod
    def truncate_snippet(cls, value: str) -> str:
        return value[:SNIPPET_MAX_LENGTH]


class SupportGrade(BaseModel):
    evidence_count: int = Field(ge=0)
    source_type_count: int = Field(ge=0, le=len(SourceType))
    level: SupportLevel
    has_divergence: bool = False


class PanelSection(BaseModel):
    key: SectionKey
    content_md: str = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    is_inference: bool = False
    divergence_note: str | None = None
    support: SupportGrade | None = None

    @model_validator(mode="after")
    def check_evidence_when_not_inference(self) -> PanelSection:
        if not self.is_inference and len(self.evidence_ids) == 0:
            raise ValueError(
                "PanelSection sem evidence_ids deve ter is_inference=True"
            )
        return self


class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    schema_version: int = 1
    theme: str = Field(min_length=2)
    theme_slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: ReportStatus = ReportStatus.RUNNING
    scope_note: str | None = None
    sections: list[PanelSection] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    degraded_sources: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)


class ReportSummary(BaseModel):
    id: str
    theme: str
    theme_slug: str
    created_at: datetime
    status: ReportStatus
    support_overview: dict[SupportLevel, int] = Field(default_factory=dict)
