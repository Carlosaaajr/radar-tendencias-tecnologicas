"""T036 — Smoke test em produção: gera os 2 temas do desafio contra Foundry + Cosmos
reais, mede duração/diversidade de fontes e verifica SC-005 (>=3 tipos de fonte).

Uso: python infra/smoke_test.py
Requer .env com PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME, COSMOS_ENDPOINT, COSMOS_KEY
preenchidos (RADAR_OFFLINE não deve estar setado — queremos gravar no Cosmos real).
"""

from __future__ import annotations

import asyncio
import io
import json
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from radar.models import ReportStatus  # noqa: E402
from radar.orchestrator import ProgressEvent, run_analysis  # noqa: E402

THEMES = ["Edge AI", "Robôs Humanoides para Indústria"]


def _print_progress(event: ProgressEvent) -> None:
    marker = "✅" if event.done else "…"
    print(f"    [{event.stage}] {marker} {event.detail}")


async def run_theme(theme: str) -> dict:
    print(f"\n=== Gerando painel: {theme} ===")
    t0 = time.monotonic()
    report = await run_analysis(theme, on_progress=_print_progress)
    elapsed = time.monotonic() - t0

    source_types = {ev.source_type.value for ev in report.evidence}
    summary = {
        "theme": theme,
        "status": report.status.value,
        "elapsed_seconds": round(elapsed, 1),
        "evidence_count": len(report.evidence),
        "source_type_count": len(source_types),
        "source_types": sorted(source_types),
        "sections_count": len(report.sections),
        "degraded_sources": report.degraded_sources,
        "warnings": report.warnings,
        "sc001_pass_5min": elapsed <= 300,
        "sc005_pass_3_types": len(source_types) >= 3,
    }

    print(f"  Status: {report.status.value} | {elapsed:.1f}s | "
          f"{len(report.evidence)} evidências | {len(source_types)} tipos de fonte "
          f"({', '.join(sorted(source_types))})")
    print(f"  SC-001 (≤5min): {'PASS' if summary['sc001_pass_5min'] else 'FAIL'} | "
          f"SC-005 (≥3 tipos): {'PASS' if summary['sc005_pass_3_types'] else 'FAIL'}")
    if report.degraded_sources:
        print(f"  ⚠️  Fontes degradadas: {report.degraded_sources}")
    if report.warnings:
        print(f"  ⚠️  Avisos: {report.warnings}")

    return summary


async def main() -> None:
    results = []
    for theme in THEMES:
        summary = await run_theme(theme)
        results.append(summary)

    out_path = Path(__file__).parent / "smoke_test_result.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultado salvo em {out_path}")

    all_completed = all(r["status"] == ReportStatus.COMPLETED.value for r in results)
    all_sc005 = all(r["sc005_pass_3_types"] for r in results)
    print(f"\n=== RESUMO: {'TODOS COMPLETOS' if all_completed else 'ALGUM FALHOU/PARCIAL'} | "
          f"SC-005 {'PASS' if all_sc005 else 'FAIL'} em todos ===")


if __name__ == "__main__":
    asyncio.run(main())
