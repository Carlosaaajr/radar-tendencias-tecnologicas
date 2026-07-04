"""Exporta relatórios do Cosmos DB para data/reports/ — demo offline (R9).

Uso: python infra/export_reports.py [tema1_slug tema2_slug ...]
Sem argumentos: exporta todos os relatórios completed/partial do Cosmos.
Requer .env com COSMOS_ENDPOINT/COSMOS_KEY (RADAR_OFFLINE não deve estar setado).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from radar.config import get_settings  # noqa: E402
from radar.models import ReportStatus  # noqa: E402
from radar.storage.cosmos import CosmosReportRepository  # noqa: E402
from radar.storage.local import LocalReportRepository  # noqa: E402


def main() -> None:
    settings = get_settings()
    if not settings.cosmos_endpoint or not settings.cosmos_key:
        print("ERRO: COSMOS_ENDPOINT/COSMOS_KEY não configurados no .env.")
        sys.exit(1)

    slugs_filter = set(sys.argv[1:]) or None

    cosmos = CosmosReportRepository(endpoint=settings.cosmos_endpoint, key=settings.cosmos_key)
    local = LocalReportRepository()

    summaries = cosmos.list_summaries()
    exported = 0
    for summary in summaries:
        if summary.status not in (ReportStatus.COMPLETED, ReportStatus.PARTIAL):
            continue
        if slugs_filter and summary.theme_slug not in slugs_filter:
            continue
        report = cosmos.get(summary.id, summary.theme_slug)
        if report is None:
            continue
        local.save(report)
        exported += 1
        print(f"Exportado: {report.theme} ({report.id})")

    print(f"\n{exported} relatório(s) exportado(s) para data/reports/.")
    print("Para usar em demo offline: defina RADAR_OFFLINE=1 no .env e rode o Streamlit local.")


if __name__ == "__main__":
    main()
