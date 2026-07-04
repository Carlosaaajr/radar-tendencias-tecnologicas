"""T006 — Spike: valida Web Search tool na nova agents API do Foundry (R1).

Roda uma pergunta real contra o projeto omc-cli/omc-ccg-cli usando o deployment
gpt-5-radar, mede latência e inspeciona o formato das citações de URL devolvidas.
Uso: python infra/spike_web_search.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from azure.identity import DefaultAzureCredential  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from azure.ai.projects import AIProjectClient  # noqa: E402

load_dotenv()

from radar.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    print(f"PROJECT_ENDPOINT={settings.project_endpoint}")
    print(f"MODEL_DEPLOYMENT_NAME={settings.model_deployment_name}")

    client = AIProjectClient(
        endpoint=settings.project_endpoint,
        credential=DefaultAzureCredential(),
    )
    openai_client = client.get_openai_client()

    question = (
        "What are the main industrial applications of Edge AI in 2026? "
        "Cite your sources with URLs."
    )

    t0 = time.monotonic()
    response = openai_client.responses.create(
        model=settings.model_deployment_name,
        input=question,
        tools=[{"type": "web_search"}],
    )
    elapsed = time.monotonic() - t0

    print(f"\n--- Latência: {elapsed:.2f}s ---\n")

    output_text = getattr(response, "output_text", None)
    print("--- output_text (primeiros 500 chars) ---")
    print((output_text or "")[:500])

    print("\n--- Estrutura de response.output (tipos de item) ---")
    citations_found = []
    for item in response.output:
        item_type = getattr(item, "type", type(item).__name__)
        print(f"  item.type={item_type}")
        content = getattr(item, "content", None)
        if not content:
            continue
        for c in content:
            annotations = getattr(c, "annotations", None) or []
            for ann in annotations:
                ann_type = getattr(ann, "type", None)
                if ann_type and "citation" in str(ann_type):
                    citations_found.append(
                        {
                            "type": str(ann_type),
                            "url": getattr(ann, "url", None),
                            "title": getattr(ann, "title", None),
                        }
                    )

    print(f"\n--- Citações extraídas: {len(citations_found)} ---")
    print(json.dumps(citations_found, indent=2, ensure_ascii=False))

    result = {
        "date": "2026-07-04",
        "project": "omc-cli/omc-ccg-cli",
        "model_deployment": settings.model_deployment_name,
        "elapsed_seconds": round(elapsed, 2),
        "citations_count": len(citations_found),
        "citations_sample": citations_found[:3],
        "output_text_preview": (output_text or "")[:300],
    }
    out_path = Path(__file__).parent / "spike_result.json"
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResultado salvo em {out_path}")


if __name__ == "__main__":
    main()
