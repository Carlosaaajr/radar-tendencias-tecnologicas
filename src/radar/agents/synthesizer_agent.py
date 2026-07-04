"""Agente Sintetizador — corpus de evidências → JSON do painel (contracts §3)."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from pydantic import ValidationError

from radar.agents.foundry import get_openai_client
from radar.config import get_settings
from radar.models import Evidence, PanelSection

MAX_RETRIES = 1


class SynthesisError(Exception):
    """Saída do LLM não pôde ser validada mesmo após retry."""


@dataclass
class SynthesisResult:
    sections: list[PanelSection] = field(default_factory=list)
    scope_note: str | None = None
    raw_warnings: list[str] = field(default_factory=list)


def _build_prompt(theme: str, corpus: dict[str, Evidence]) -> str:
    numbered = "\n".join(
        f"[{eid}] ({ev.source_type.value}) {ev.title} — {ev.snippet}"
        for eid, ev in corpus.items()
    )
    return f"""Você é um analista que consolida evidências sobre uma tendência tecnológica
industrial em um painel executivo, em português brasileiro.

Tema: {theme}

Evidências numeradas (cite pelo id entre colchetes, ex.: [ev-1], em cada afirmação
factual):
{numbered}

Gere um JSON com a chave "sections" (lista) e opcionalmente "scope_note". Cada seção
tem: key (uma de: definition, maturity, applications, sectors, players, investments,
adoption_signals, opportunities, risks, outlook), content_md, evidence_ids (lista de ids
citados), is_inference (true se não houver evidência direta), divergence_note (texto ou
null, preenchido quando as fontes discordam). NUNCA afirme algo sem citar um id existente;
se não houver lastro, marque is_inference=true e evidence_ids=[]."""


def parse_synthesis_output(raw: dict, corpus: dict[str, Evidence]) -> SynthesisResult:
    if "sections" not in raw:
        raise SynthesisError("Campo obrigatório 'sections' ausente na saída do LLM")

    warnings: list[str] = []
    sections: list[PanelSection] = []

    for raw_section in raw["sections"]:
        evidence_ids = list(raw_section.get("evidence_ids", []))
        is_inference = bool(raw_section.get("is_inference", False))

        orphan_ids = [eid for eid in evidence_ids if eid not in corpus]
        if orphan_ids:
            warnings.append(
                f"Seção '{raw_section.get('key')}' citava id(s) inexistente(s) "
                f"{orphan_ids}; rebaixada a inferência."
            )
            evidence_ids = [eid for eid in evidence_ids if eid in corpus]
            is_inference = True

        try:
            section = PanelSection(
                key=raw_section["key"],
                content_md=raw_section["content_md"],
                evidence_ids=evidence_ids,
                is_inference=is_inference,
                divergence_note=raw_section.get("divergence_note"),
            )
        except (KeyError, ValidationError) as exc:
            raise SynthesisError(f"Seção inválida na saída do LLM: {exc}") from exc

        sections.append(section)

    return SynthesisResult(
        sections=sections,
        scope_note=raw.get("scope_note"),
        raw_warnings=warnings,
    )


async def synthesize(
    theme: str, corpus: list[Evidence], *, timeout_s: float = 120
) -> SynthesisResult:
    corpus_by_id = {ev.id: ev for ev in corpus}
    prompt = _build_prompt(theme, corpus_by_id)
    settings = get_settings()
    client = get_openai_client()

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        instructions = prompt
        if attempt > 0 and last_error is not None:
            instructions += (
                f"\n\nATENÇÃO: a resposta anterior falhou na validação "
                f"({last_error}). Responda apenas com o JSON válido descrito acima."
            )
        response = await asyncio.to_thread(
            client.responses.create,
            model=settings.model_deployment_name,
            input=instructions,
            text={"format": {"type": "json_object"}},
            timeout=timeout_s,
        )
        try:
            raw = json.loads(response.output_text)
            return parse_synthesis_output(raw, corpus_by_id)
        except (json.JSONDecodeError, SynthesisError) as exc:
            last_error = exc
            continue

    raise SynthesisError(f"Falha na síntese após {MAX_RETRIES + 1} tentativas: {last_error}")
