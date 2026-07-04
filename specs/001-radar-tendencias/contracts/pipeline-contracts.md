# Pipeline Contracts — módulos internos

**Date**: 2026-07-03 | **Feature**: 001-radar-tendencias

Contratos entre os módulos do pipeline (assinaturas Python — `src/radar/`). A UI
(Streamlit) consome apenas `Orchestrator` e `ReportRepository`.

## 1. Collector (protocolo — `collectors/base.py`)

```python
class Collector(Protocol):
    name: str                      # "arxiv", "openalex"
    source_type: SourceType        # tipo atribuído às evidências

    async def collect(self, theme: str, *, limit: int = 10,
                      timeout_s: float = 30) -> CollectorResult
```

```python
@dataclass
class CollectorResult:
    evidence: list[Evidence]       # pode ser vazia
    degraded: bool                 # True se a fonte falhou/limitou
    error: str | None              # motivo da degradação (log/painel)
```

**Regras**: `collect` NUNCA propaga exceção (FR-012) — captura e devolve
`degraded=True`. Evidência sem URL é descartada aqui. `snippet` truncado a 500
caracteres. Timeout individual por fonte.

## 2. CollectorAgent (Foundry — `agents/collector_agent.py`)

```python
async def run_market_collection(theme: str, *, perspectives: list[str],
                                timeout_s: float) -> CollectorResult
```

- Cria/reusa agente Foundry com `BingGroundingTool` (connection via
  `BING_CONNECTION_ID`).
- Prompt gera **4 perguntas** (uma por perspectiva: `technical`, `economic`,
  `industrial`, `regulatory` — R2) e responde cada uma com busca groundada.
- Converte **URL citations** da resposta em `Evidence` (source_type inferido:
  `market`/`news`/`corporate`/`patent` por heurística de domínio; default `news`).
- Mesmo contrato de degradação do Collector (falha do Foundry → `degraded=True`).

## 3. SynthesizerAgent (`agents/synthesizer_agent.py`)

```python
async def synthesize(theme: str, corpus: list[Evidence],
                     *, timeout_s: float) -> SynthesisResult
```

```python
@dataclass
class SynthesisResult:
    sections: list[PanelSection]   # support ainda NÃO preenchido
    scope_note: str | None
    raw_warnings: list[str]
```

**Regras**:
- Entrada: corpus numerado (`ev-1`...`ev-N`) com snippets; instrução: só afirmar com
  citação `evidence_ids`; sem lastro → `is_inference=true`; divergências →
  `divergence_note`; saída em pt-BR.
- Saída do LLM validada contra subconjunto do `report-schema.json` (sections). JSON
  inválido → 1 retry com mensagem de correção → falha vira exceção tipada
  `SynthesisError` (orquestrador decide `partial`/`failed`).
- `evidence_ids` citando id inexistente → seção rebaixada a `is_inference=true` +
  warning (validação em código, não confiança no LLM).

## 4. Grading (`synthesis/grading.py`) — puro/determinístico

```python
def grade_section(section: PanelSection, corpus: dict[str, Evidence]) -> SupportGrade
def grade_report(sections, corpus) -> list[PanelSection]   # preenche .support
```

Regras R8 (função total — toda combinação classificada): `high` = ≥4 evidências E ≥2
tipos; `medium` = 2-3 evidências, OU ≥4 evidências com <2 tipos; `low` = 1; `inference` = 0.

## 5. Dedup (`synthesis/dedup.py`) — puro/determinístico

```python
def dedup_evidence(items: list[Evidence]) -> list[Evidence]
```

URL normalizada (scheme/host lowercase, sem tracking params, sem trailing slash) +
título normalizado (casefold, sem pontuação) com similaridade ≥ 0.9 → duplicata;
mantém a de metadados mais ricos (FR-007).

## 6. Orchestrator (`orchestrator.py`)

```python
async def run_analysis(theme: str, *, on_progress: Callable[[ProgressEvent], None],
                       budget_s: float = 360) -> Report
```

```python
@dataclass
class ProgressEvent:
    stage: Literal["academic", "market", "synthesis", "grading", "saving"]
    detail: str                    # ex.: "arXiv: 8 evidências"
    done: bool
```

**Sequência**: persiste documento `status=running` → coletas acadêmica + mercado
(concorrentes, `asyncio.gather`) → dedup → synthesize → grading → atualiza documento
final. Budget global `budget_s` (FR-013): estouro → salva `status=partial` com warning.
Todas as fontes degradadas e corpus vazio → `status=failed`. `on_progress` alimenta a
UI (FR-008).

**Guardas**: antes de iniciar, verifica limite diário de análises
(`MAX_ANALYSES_PER_DAY`, default 10 — R10) → excedido, lança `RateLimitExceeded` com
mensagem amigável na UI. A UI usa `st.session_state` para não reiniciar pipeline em
rerun acidental; o documento `running` inicial garante que queda de WebSocket não perde
a execução.

## 7. ReportRepository (interface em `storage/base.py`)

```python
class ReportRepository(Protocol):
    def save(self, report: Report) -> None
    def get(self, report_id: str, theme_slug: str) -> Report | None   # point read
    def list_summaries(self) -> list[ReportSummary]      # projeção leve (SC-003)
    def find_by_slug(self, theme_slug: str) -> list[ReportSummary]  # FR-011
```

Implementações: `CosmosReportRepository` (`storage/cosmos.py`, produção) e
`LocalReportRepository` (`storage/local.py`, demo offline — R9; mesmos documentos JSON
em `data/reports/`, selecionada por `RADAR_OFFLINE=1`).

`ReportSummary`: `id`, `theme`, `theme_slug`, `created_at`, `status`,
`support_overview` (contagem de seções por nível). `theme_slug` no summary permite
point read (`read_item(id, partition_key=theme_slug)`) em vez de query cross-partition.
Erro de Cosmos na leitura do histórico → UI mostra mensagem clara; na escrita → retry
1x e warning (relatório ainda exibido em memória).

## 8. UI ↔ pipeline

- `Home.py`: chama `run_analysis` com callback de progresso; ao concluir, redireciona
  para o painel renderizado; se `find_by_slug` encontra relatório anterior do tema,
  oferece reabrir ou regenerar (FR-011).
- `1_Historico.py`: `list_summaries()` → tabela; abrir → `get(id)` (FR-009/010).
- `2_Evidencias.py`: recebe `Report` da sessão; filtros por `source_type` (FR-015).
