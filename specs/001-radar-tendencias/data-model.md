# Data Model: Radar de Tendências Tecnológicas

**Date**: 2026-07-03 | **Feature**: 001-radar-tendencias

Modelos Pydantic em `src/radar/models.py`; persistidos como **um documento agregado por
relatório** no Cosmos DB (container `reports`, partition key `/theme_slug`).

## Evidence (Evidência)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | str | `ev-{seq}` único dentro do relatório |
| `title` | str | obrigatório |
| `source_type` | enum | `scientific` \| `market` \| `news` \| `corporate` \| `patent` |
| `origin` | str | ex.: "arXiv", "OpenAlex", "Bing: MIT Tech Review" |
| `url` | str (URL) | obrigatório; usado no link clicável (SC-006) |
| `published_at` | date \| null | quando disponível (FR-006) |
| `snippet` | str | trecho/resumo relevante; **truncado a 500 caracteres na coleta** (limite de 2 MB/item do Cosmos) |
| `language` | str | ISO 639-1 (`en`, `pt`, ...) |
| `perspective` | str \| null | perspectiva STORM que a originou (só coleta de mercado) |
| `citation_count` | int \| null | só evidências acadêmicas (OpenAlex) |

**Validação**: URL obrigatória e não vazia — evidência sem URL é descartada na coleta
(Princípio I). Deduplicação por URL normalizada e por similaridade de título (FR-007).

## PanelSection (Seção do Painel)

| Campo | Tipo | Regras |
|---|---|---|
| `key` | enum | uma das 10 seções (abaixo) |
| `content_md` | str | texto analítico em pt-BR (FR-014), markdown |
| `evidence_ids` | list[str] | ids citados; PODE ser vazia somente se `is_inference=true` |
| `is_inference` | bool | true quando sem lastro em evidência (FR-006) |
| `divergence_note` | str \| null | preenchida quando fontes conflitam (US3-c3) |
| `support` | SupportGrade | calculado, nunca vindo do LLM (R8) |

**Seções (`key`)**: `definition`, `maturity`, `applications`, `sectors`, `players`,
`investments`, `adoption_signals`, `opportunities`, `risks`, `outlook` (FR-004).

## SupportGrade (Grau de Suporte) — objeto calculado

| Campo | Tipo | Regras |
|---|---|---|
| `evidence_count` | int | nº de evidências citadas na seção (pós-dedup) |
| `source_type_count` | int | nº de `source_type` distintos |
| `level` | enum | `high` (≥4 evid. E ≥2 tipos) \| `medium` (2-3 evid., OU ≥4 com <2 tipos) \| `low` (1) \| `inference` (0) — regra total: toda combinação classificada |
| `has_divergence` | bool | espelha `divergence_note != null` |

**Regra**: computado por `synthesis/grading.py` a partir de `evidence_ids` — determinístico
e testável (R8).

## Report (Relatório / Painel Executivo) — documento raiz no Cosmos

| Campo | Tipo | Regras |
|---|---|---|
| `id` | str | uuid4 |
| `theme` | str | texto informado pelo usuário (FR-001) |
| `theme_slug` | str | partition key; slug do tema normalizado |
| `created_at` | datetime | UTC |
| `status` | enum | `running` \| `completed` \| `partial` \| `failed` |
| `scope_note` | str \| null | recorte adotado p/ tema ambíguo (edge case) |
| `sections` | list[PanelSection] | 10 itens quando `completed`; subconjunto se `partial` |
| `evidence` | list[Evidence] | corpus completo pós-dedup |
| `degraded_sources` | list[str] | categorias indisponíveis na execução (FR-012) |
| `warnings` | list[str] | baixa sustentação, timeout parcial etc. (FR-013, US1-c4) |
| `metrics` | dict | duração por etapa, contagens por fonte (avaliação crítica/custos) |

**Transições de estado**: `running → completed` | `running → partial` (timeout ou
degradação severa) | `running → failed` (falha total). Documentos `failed` guardam o
erro em `warnings`; histórico exibe apenas `completed`/`partial` (FR-009), com aviso
visual para `partial`.

**Consulta de histórico**: `SELECT id, theme, theme_slug, created_at, status, resumo de
support` — projeção leve; `theme_slug` incluído para que a abertura do relatório seja
**point read** (`read_item(id, partition_key=theme_slug)`), não query cross-partition;
documento completo carregado só ao abrir (SC-003).

**Relacionamentos**: `PanelSection.evidence_ids → Evidence.id` (intra-documento).
Integridade validada por Pydantic antes de persistir: todo `evidence_id` citado deve
existir no corpus; citação órfã → afirmação rebaixada a `is_inference=true` + warning.
