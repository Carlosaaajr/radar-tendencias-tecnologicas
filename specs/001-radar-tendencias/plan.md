# Implementation Plan: Radar de Tendências Tecnológicas

**Branch**: `001-radar-tendencias` | **Date**: 2026-07-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-radar-tendencias/spec.md`

## Summary

Plataforma web (Streamlit) que recebe um tema tecnológico e gera painel executivo com 10
seções, cada uma com grau de suporte calculado deterministicamente a partir de evidências
citadas. Pipeline em 3 estágios: (1) coleta acadêmica determinística (arXiv + OpenAlex via
HTTP), (2) coleta de mercado via Agente Coletor no Azure AI Foundry (Grounding with Bing
Search + perguntas multi-perspectiva estilo STORM), (3) consolidação via Agente
Sintetizador (saída JSON validada por schema). Relatórios persistidos como documento único
no Cosmos DB serverless; histórico abre sem nova coleta. Detalhes e justificativas em
[research.md](./research.md).

## Technical Context

**Language/Version**: Python 3.11+ (runtime nativo do App Service Linux)

**Primary Dependencies**: `streamlit` (UI), `azure-ai-projects` + `azure-ai-agents`
(Foundry Agent Service, BingGroundingTool), `azure-identity` (DefaultAzureCredential),
`azure-cosmos` (persistência), `httpx` (arXiv/OpenAlex), `pydantic` (schemas do painel e
evidências), `python-dotenv` (config local), `feedparser` (Atom do arXiv)

**Storage**: Azure Cosmos DB serverless (API NoSQL) — database `radar`, container
`reports` (partition key `/theme_slug`); relatório = documento agregado único (painel +
evidências + graus de suporte)

**Testing**: `pytest` + `respx` (mocks HTTP) + fixtures JSON; smoke test live opcional
(`@pytest.mark.live`)

**Target Platform**: Azure App Service Linux (plano B1), startup command
`python -m streamlit run app/Home.py --server.port 8000 --server.address 0.0.0.0`;
agentes no projeto Azure AI Foundry existente (modelo GPT-4.1 — Bing grounding é
incompatível com gpt-4o-mini/gpt-5)

**Project Type**: Web application single-project (UI + pipeline no mesmo deploy;
Streamlit chama o orquestrador in-process — sem API separada no MVP)

**Performance Goals**: painel completo ≤ 5 min (SC-001); histórico < 5 s (SC-003);
progresso por etapa visível durante a execução (FR-008)

**Constraints**: falha de fonte não aborta pipeline (FR-012); timeout global da análise
com entrega parcial (FR-013, default 6 min); painel em pt-BR (FR-014); toda afirmação
rastreável ou marcada inferência (FR-006); demo executável de cache offline (Princípio IV,
incluindo modo `RADAR_OFFLINE=1` com repositório em disco — R9); controle de abuso de
custo: Access Restrictions + `MAX_ANALYSES_PER_DAY` + budget alert (R10); autenticação em
produção via Managed Identity + role "Azure AI User" no projeto Foundry (R1)

**Scale/Scope**: usuário único, dezenas de relatórios, ~15-40 evidências por relatório;
documento Cosmos < 2 MB

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como o plano atende | Status |
|---|---|---|
| I. Evidência Rastreável | Evidências tipadas com URL/data; grau de suporte calculado em código a partir das citações (R8); Sintetizador obrigado a citar `evidence_id` por afirmação; afirmações sem citação → marcadas `inference` | ✅ |
| II. Simplicidade | Single-project, orquestração in-process (sem API/fila/worker); sem framework de agentes além do SDK Foundry; STORM como técnica de prompt, não dependência (R2) | ✅ |
| III. Azure-First | App Service + Cosmos serverless + Foundry Agent Service; segredos via App Settings/env (R6); Managed Identity + RBAC p/ Foundry em produção (R1); controle de abuso: Access Restrictions, limite diário, budget alert (R10); únicas saídas do Azure: arXiv/OpenAlex (fontes públicas, permitidas) | ✅ |
| IV. Resiliência de Demo | Relatório persistido no início (`running`) e ao concluir; coleta por fonte em try/except com degradação registrada; UI abre histórico sem rede; timeout com entrega parcial; **modo offline local** (`RADAR_OFFLINE=1`, repositório em disco — R9) cobre queda de rede no local da apresentação | ✅ |
| V. Qualidade Avaliável | Módulos `collectors/`, `agents/`, `synthesis/`, `storage/`, `app/`; pytest nos módulos críticos (R7); docs/architecture.md com diagrama; README reproduzível | ✅ |
| VI. Avaliação Crítica | `docs/critical-review.md` criado no plano e atualizado por fase (custos por consulta, vieses de fonte/idioma/modelo, limitações, evoluções) | ✅ |

**Post-design re-check** (após Phase 1): sem violações novas — contratos e modelo de
dados mantêm documento único e pipeline sequencial. Complexity Tracking vazio.

**Revisão de arquitetura (octo-cloud-architect, 2026-07-04)**: veredito **APROVADO COM
AJUSTES** — 6 ajustes obrigatórios aplicados (Managed Identity/RBAC, controle de abuso,
deprecação da plataforma classic + spike dia 1, modo offline local, regra de graduação
totalizada, operação Streamlit/App Service). Estimativa FinOps registrada em
`docs/critical-review.md`: ~US$14-15/mês fixo + ~US$0,30-0,60 por análise.

## Project Structure

### Documentation (this feature)

```text
specs/001-radar-tendencias/
├── plan.md              # Este arquivo
├── research.md          # Phase 0 — decisões R1-R8
├── data-model.md        # Phase 1 — entidades e schema do documento
├── quickstart.md        # Phase 1 — rodar local + provisionar Azure
├── contracts/
│   ├── report-schema.json    # Schema do painel (saída do Sintetizador / doc Cosmos)
│   └── pipeline-contracts.md # Contratos entre módulos do pipeline
└── tasks.md             # Phase 2 (/speckit-tasks — não criado por /speckit-plan)
```

### Source Code (repository root)

```text
app/
├── Home.py                  # Página principal: input do tema + execução com progresso
├── pages/
│   ├── 1_Historico.py       # Lista e reabre relatórios (FR-009/010/011)
│   └── 2_Evidencias.py      # Exploração de evidências com filtros (FR-015)
└── components/
    ├── panel.py             # Render das 10 seções + badges de grau de suporte
    └── progress.py          # Progresso por etapa (FR-008)

src/radar/
├── config.py                # Settings (pydantic-settings, env vars)
├── models.py                # Pydantic: Evidence, PanelSection, Report, SupportGrade
├── orchestrator.py          # Pipeline: coleta → síntese → graduação → persistência
├── collectors/
│   ├── base.py              # Protocolo Collector + degradação graciosa (FR-012)
│   ├── arxiv.py             # arXiv API (Atom)
│   └── openalex.py          # OpenAlex API (JSON)
├── agents/
│   ├── foundry.py           # Criação/reuso dos agentes no Foundry (idempotente)
│   ├── collector_agent.py   # Agente Coletor: perguntas multi-perspectiva + Bing
│   └── synthesizer_agent.py # Agente Sintetizador: corpus → JSON do painel
├── synthesis/
│   ├── dedup.py             # Deduplicação de evidências (FR-007)
│   └── grading.py           # Grau de suporte determinístico (R8, FR-005)
└── storage/
    ├── base.py              # Interface ReportRepository
    ├── cosmos.py            # Repositório Cosmos DB (produção)
    └── local.py             # Repositório em disco p/ demo offline (R9)

tests/
├── unit/                    # dedup, grading, parsing de schemas, collectors (mock)
├── integration/             # pipeline com agentes mockados; storage com emulador/mock
└── fixtures/                # JSONs de arXiv/OpenAlex/respostas de agentes

docs/
├── architecture.md          # Diagrama + decisões (Princípio V)
└── critical-review.md       # Custos, vieses, limitações, evoluções (Princípio VI)

infra/
└── provision.md             # Passos az cli p/ App Service, Cosmos, Bing grounding
```

**Structure Decision**: single-project Python. Streamlit (`app/`) importa o pacote
`src/radar/` in-process — sem API HTTP interna, sem workers. Justificativa: usuário
único, pipeline sequencial, prazo de 1 semana (Princípio II). A separação `app/` vs
`src/radar/` mantém o pipeline testável sem Streamlit e permitiria extrair API depois
(evolução futura declarada).

## Complexity Tracking

Sem violações da constituição — tabela vazia.
