# Tasks: Radar de Tendências Tecnológicas

**Input**: Design documents from `/specs/001-radar-tendencias/`

**Prerequisites**: plan.md, spec.md, research.md (R1-R10), data-model.md, contracts/, quickstart.md

**Tests**: INCLUÍDOS — a constituição (Princípio V) exige testes nos módulos críticos do
pipeline: dedup, grading, parsing/validação das respostas dos agentes e fallbacks de coleta.

**Organization**: Tarefas agrupadas por user story (US1 gera painel; US2 histórico/cache;
US3 exploração de evidências), com Setup e Foundational antes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: paralelizável (arquivos diferentes, sem dependência pendente)
- **[Story]**: US1, US2, US3 — somente nas fases de user story

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Estrutura do projeto e ferramentas

- [X] T001 Create project skeleton per plan.md: dirs `app/pages/`, `app/components/`, `src/radar/{collectors,agents,synthesis,storage}/`, `tests/{unit,integration,fixtures}/`, `docs/`, `infra/`, `data/reports/.gitkeep`, with `__init__.py` files
- [X] T002 Create `requirements.txt` (pinned: streamlit, azure-ai-projects, azure-identity, azure-cosmos, httpx, pydantic, pydantic-settings, python-dotenv, feedparser) and `requirements-dev.txt` (pytest, pytest-asyncio, respx, ruff); create venv and install
- [X] T003 [P] Create `.env.example` (all vars from quickstart.md §1), `.gitignore` (.env, .venv, data/reports/*.json, __pycache__), `.streamlit/config.toml` (headless, proxy-safe settings per R4)
- [X] T004 [P] Configure `pyproject.toml` with ruff (lint+format) and pytest settings (asyncio mode, `live` marker excluded by default)
- [X] T005 [P] Create `README.md` skeleton: o que é, arquitetura em 1 parágrafo, como rodar local, como testar, como fazer deploy (links p/ quickstart e docs/)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Spike de risco + núcleo compartilhado que TODAS as stories usam

**⚠️ CRITICAL**: Nenhuma user story começa antes desta fase terminar

- [ ] T006 **SPIKE DIA 1 (gate de risco — R1, caminho já decidido)**: script `infra/spike_web_search.py` que cria agente com Web Search tool no projeto Foundry `omc-cli/omc-ccg-cli` usando o deployment `gpt-5-radar`, roda 1 pergunta, valida formato das citações de URL e mede latência; registrar resultado em `docs/critical-review.md`. **Se falhar: parar e revisitar R1** (não há mais fallback de plataforma — Bing Grounding classic está descartado por bloqueio de assinatura, ver research.md R1)
- [ ] T007 [P] Implement Pydantic models in `src/radar/models.py`: Evidence (snippet ≤500 chars, URL obrigatória), PanelSection, SupportGrade, Report, ReportSummary, enums SourceType/SectionKey/ReportStatus/SupportLevel — conforme data-model.md e report-schema.json
- [ ] T008 [P] Implement settings in `src/radar/config.py` (pydantic-settings): PROJECT_ENDPOINT, MODEL_DEPLOYMENT_NAME (default gpt-5-radar), COSMOS_ENDPOINT/KEY, ANALYSIS_BUDGET_SECONDS=360, MAX_ANALYSES_PER_DAY=10, RADAR_OFFLINE flag
- [ ] T009 [P] Define `ReportRepository` protocol in `src/radar/storage/base.py` (save, get(id, theme_slug) point read, list_summaries, find_by_slug) per contracts §7
- [ ] T010 Implement `LocalReportRepository` in `src/radar/storage/local.py` (JSON files em `data/reports/` — R9; usado também pelos testes) + unit test `tests/unit/test_local_repo.py`
- [ ] T011 Implement `CosmosReportRepository` in `src/radar/storage/cosmos.py` (point read, projeção leve no list_summaries, retry 1x na escrita) + factory por RADAR_OFFLINE em `src/radar/storage/__init__.py`
- [ ] T012 [P] Define `Collector` protocol + `CollectorResult` in `src/radar/collectors/base.py` (nunca propaga exceção, degraded/error, timeout por fonte — contracts §1)
- [ ] T013 [P] Create test fixtures in `tests/fixtures/`: arxiv_atom.xml, openalex_response.json, agent_citations.json, synthesizer_output.json (válido e inválido)

**Checkpoint**: spike validado + modelos/storage/protocolos prontos — stories podem começar

---

## Phase 3: User Story 1 - Gerar painel executivo a partir de um tema (Priority: P1) 🎯 MVP

**Goal**: Tema em texto livre → painel com 10 seções, grau de suporte calculado em código
e referências verificáveis; progresso por etapa; degradação graciosa; timeout parcial.

**Independent Test**: informar "Edge AI" e verificar painel completo com badges de suporte
e referências clicáveis; simular falha de fonte e verificar conclusão com aviso (spec US1).

### Tests for User Story 1 (módulos críticos — Princípio V; escrever ANTES da implementação)

- [ ] T014 [P] [US1] Unit tests dedup in `tests/unit/test_dedup.py`: URL normalizada (tracking params, trailing slash, case), título similar ≥0.9, mantém metadados mais ricos (FR-007)
- [ ] T015 [P] [US1] Unit tests grading in `tests/unit/test_grading.py`: regra TOTAL de R8 — high (≥4 E ≥2 tipos), medium (2-3 OU ≥4 com <2 tipos), low (1), inference (0), divergência
- [ ] T016 [P] [US1] Unit tests collectors in `tests/unit/test_collectors.py` (respx): parsing arXiv/OpenAlex das fixtures, timeout → degraded=True sem exceção, evidência sem URL descartada, snippet truncado a 500
- [ ] T017 [P] [US1] Unit tests synthesizer parsing in `tests/unit/test_synthesizer_parsing.py`: saída válida vs inválida contra report-schema.json, retry 1x, evidence_id órfão → is_inference=true + warning (contracts §3)

### Implementation for User Story 1

- [ ] T018 [P] [US1] Implement arXiv collector in `src/radar/collectors/arxiv.py` (Atom via httpx+feedparser, source_type=scientific)
- [ ] T019 [P] [US1] Implement OpenAlex collector in `src/radar/collectors/openalex.py` (JSON, mailto param, citation_count, source_type=scientific)
- [ ] T020 [P] [US1] Implement dedup in `src/radar/synthesis/dedup.py` (contracts §5)
- [ ] T021 [P] [US1] Implement grading in `src/radar/synthesis/grading.py` (contracts §4, função pura)
- [ ] T022 [US1] Implement Foundry agent lifecycle in `src/radar/agents/foundry.py`: criação idempotente (get-or-create por nome) do Coletor (Web Search tool) e Sintetizador, conforme validado no spike T006
- [ ] T023 [US1] Implement CollectorAgent in `src/radar/agents/collector_agent.py`: 4 perguntas (1 por perspectiva R2), busca cobrindo pt e en (edge case de idioma), URL citations → Evidence (heurística de domínio p/ source_type), degradação graciosa (contracts §2)
- [ ] T024 [US1] Implement SynthesizerAgent in `src/radar/agents/synthesizer_agent.py`: prompt pt-BR com corpus numerado, citação obrigatória por afirmação, divergence_note, validação por schema + retry (contracts §3)
- [ ] T025 [US1] Implement orchestrator in `src/radar/orchestrator.py`: guarda MAX_ANALYSES_PER_DAY → doc `running` persistido → gather(acadêmico, mercado) → dedup → synthesize → grading → save final; budget com entrega parcial; corpus vazio → failed; corpus pequeno (< 5 evidências pós-dedup) → warning de baixa sustentação no Report (US1-cenário 4); ProgressEvent callbacks (contracts §6)
- [ ] T026 [US1] Integration test pipeline in `tests/integration/test_pipeline.py` (agentes/HTTP mockados): fluxo feliz, uma fonte degradada → completed com degraded_sources, mercado inteiro degradado mas acadêmico ok → completed (corpus só acadêmico é válido — FR-012), todas degradadas → failed, timeout → partial (FR-013)
- [ ] T027 [P] [US1] Implement panel component in `app/components/panel.py`: 10 seções, badges de suporte (Alto/Médio/Baixo/Inferência), referências clicáveis (≤2 cliques — SC-006), avisos de degradação/parcial, divergence_note
- [ ] T028 [P] [US1] Implement progress component in `app/components/progress.py` (etapas: acadêmica, mercado, consolidação, graduação, salvando — FR-008)
- [ ] T029 [US1] Implement `app/Home.py`: input do tema, st.session_state guard contra rerun (R4), chama orchestrator com callback, renderiza painel ao concluir, erros amigáveis (RateLimitExceeded, falha total)

**Checkpoint**: US1 completa — gerar painel de "Edge AI" end-to-end (com credenciais reais) e via testes mockados

---

## Phase 4: User Story 2 - Consultar histórico e reabrir relatórios (Priority: P2)

**Goal**: Histórico com resumo de suporte; reabertura instantânea sem coleta; oferta
reabrir-ou-regenerar para tema repetido; base da resiliência de demo.

**Independent Test**: gerar 2 relatórios, reiniciar app, ver histórico e abrir ambos
offline (< 5 s — SC-003); repetir tema e receber a oferta de reabrir/regenerar.

### Implementation for User Story 2

- [ ] T030 [P] [US2] Implement `app/pages/1_Historico.py`: list_summaries em tabela (tema, data, status, support_overview), abrir via point read, aviso visual p/ `partial` (FR-009/010)
- [ ] T031 [US2] Add reopen-or-regenerate flow in `app/Home.py`: find_by_slug antes de rodar pipeline; se existir, oferecer reabrir ou gerar nova análise (FR-011)
- [ ] T032 [P] [US2] Create export script `infra/export_reports.py`: Cosmos → `data/reports/*.json` p/ demo offline (R9) + instrução no README
- [ ] T033 [US2] Integration test in `tests/integration/test_history.py`: salvar → listar → reabrir com LocalReportRepository; find_by_slug com tema repetido

**Checkpoint**: US1 + US2 funcionam; demo já sobrevive a falha de rede (RADAR_OFFLINE=1)

---

## Phase 5: User Story 3 - Explorar as evidências em detalhe (Priority: P3)

**Goal**: Visão completa das evidências com filtros por tipo e destaque de divergências.

**Independent Test**: abrir relatório gerado, filtrar por tipo de fonte, conferir contagem
por categoria e exibição de divergências (spec US3).

### Implementation for User Story 3

- [ ] T034 [US3] Implement `app/pages/2_Evidencias.py`: relatório vindo da sessão (fluxo do painel) com fallback para seleção do histórico; lista completa (título, tipo, origem, data, link), filtro por source_type com contagem por categoria, seções com divergence_note destacadas (FR-015)

**Checkpoint**: as 3 stories funcionam de forma independente

---

## Phase 6: Polish, Deploy & Apresentação

**Purpose**: Deploy Azure, documentação da banca, revisão de código e ensaio de demo

- [ ] T035 [P] Write `infra/provision.md` + provisionar Azure conforme quickstart.md §3: RG, Cosmos serverless (radar/reports), App Service B1 (Always On, startup command, App Settings), **Managed Identity + role "Azure AI User"**, Access Restrictions, budget alert (R10)
- [ ] T036 Deploy app no App Service e smoke test em produção: gerar relatório real p/ os 2 temas do desafio, verificar `source_type_count ≥ 3` no agregado (SC-005), medir duração/custos via campo `metrics` e atualizar estimativas em `docs/critical-review.md`
- [ ] T037 [P] Write `docs/architecture.md`: diagrama (mermaid) UI→orquestrador→agentes/coletas→Cosmos, decisões técnicas com justificativa e referência a R1-R10 (Princípio V)
- [ ] T038 [P] Update `docs/critical-review.md` com números medidos (latência por etapa, tokens, custo real/análise) e limitações observadas (Princípio VI)
- [ ] T039 Code review pelo agente **octo-code-reviewer** (gate da constituição) cobrindo `src/radar/` e `app/`; aplicar correções obrigatórias
- [ ] T040 Preparar demo (quickstart §4): gerar e exportar 2-3 relatórios (Edge AI, Robôs Humanoides p/ Indústria), testar RADAR_OFFLINE=1 no notebook, ensaiar roteiro de 10 min, liberar IP do local nas Access Restrictions
- [ ] T041 [P] Finalize `README.md`: instruções reproduzíveis completas (rodar, testar, deploy, demo offline) — Princípio V

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (P1)**: sem dependências
- **Foundational (P2)**: após Setup — **T006 (spike) é gate**: falha → replanejar R1 antes de qualquer story
- **US1 (P3)**: após Foundational — MVP; nenhuma dependência de outra story
- **US2 (P4)**: após Foundational; usa Report/repository (já foundational); integra com Home.py (T031 depende de T029)
- **US3 (P5)**: após Foundational; lê Report da sessão (T034 depende de T027 apenas para navegação — testável com relatório carregado do repositório)
- **Polish (P6)**: T035 pode começar cedo em paralelo (não depende de código); T036 depende de US1 + T035; T039-T041 por último

### Within User Story 1

Tests T014-T017 ANTES de T018-T025 (devem falhar primeiro). T018-T021 paralelos.
T022 → T023/T024 → T025 → T026. UI T027-T028 paralelos após T025; T029 fecha.

### Parallel Opportunities

- Setup: T003, T004, T005 em paralelo após T002
- Foundational: T007, T008, T009, T012, T013 em paralelo; T006 em paralelo com todos (só exige .env)
- US1: os 4 arquivos de teste em paralelo; os 4 módulos puros (T018-T021) em paralelo
- Polish: T035, T037, T038, T041 em paralelo

---

## Implementation Strategy

**MVP first (calibrado ao prazo < 1 semana)**:

1. Dia 1: Setup + Foundational — **spike T006 decide o caminho dos agentes**
2. Dias 2-3: US1 completa (testes → módulos puros → agentes → orquestrador → UI) → **MVP demonstrável**
3. Dia 4: US2 (histórico + offline) + provisionamento Azure (T035)
4. Dia 5: US3 + deploy (T036) + docs (T037/T038)
5. Dia 6: review octo-code-reviewer (T039) + preparação de demo (T040/T041) + folga p/ imprevistos

Cada checkpoint entrega incremento demonstrável — se o prazo apertar, US3 é cortável sem
comprometer o núcleo do desafio (painel + histórico + resiliência).

## Notes

- Commits ao fim de cada tarefa ou grupo lógico (hooks git do speckit)
- Segredos APENAS via .env/App Settings (Princípio III) — nunca em código ou fixtures
- `pytest` (mockado) deve passar em todo checkpoint; `pytest -m live` só com credenciais
