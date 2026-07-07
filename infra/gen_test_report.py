"""Gera 1 relatório real (coleta + síntese ao vivo) salvo localmente para testar os
gráficos novos do painel executivo, sem tocar o Cosmos de produção.

Uso: RADAR_OFFLINE=1 python infra/gen_test_report.py "Tema aqui"
"""

from __future__ import annotations

import asyncio
import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from radar.orchestrator import ProgressEvent, run_analysis  # noqa: E402


def _print_progress(event: ProgressEvent) -> None:
    marker = "OK" if event.done else "..."
    print(f"    [{event.stage}] {marker} {event.detail}")


async def main(theme: str) -> None:
    print(f"=== Gerando painel: {theme} ===")
    t0 = time.monotonic()
    report = await run_analysis(theme, on_progress=_print_progress)
    elapsed = time.monotonic() - t0
    print(f"\nStatus: {report.status.value} | {elapsed:.1f}s | "
          f"{len(report.evidence)} evidências | {len(report.sections)} seções")
    print(f"Report ID: {report.id}")


_DEFAULT_THEME = "Manutenção assistida por IA Generativa e Multiagentes de IA"

if __name__ == "__main__":
    theme = sys.argv[1] if len(sys.argv) > 1 else _DEFAULT_THEME
    asyncio.run(main(theme))
