# Radar de Tendências Tecnológicas

Plataforma que recebe um tema tecnológico (ex.: "Edge AI", "Robôs Humanoides para
Indústria") e gera um painel executivo estruturado, fundamentado em evidências
verificáveis coletadas na internet — desenvolvida para o desafio **SENAI do Futuro — IA**.

## Arquitetura em 1 parágrafo

Streamlit no Azure App Service orquestra um pipeline em Python que combina coleta
acadêmica determinística (arXiv, OpenAlex) com um Agente Coletor no Azure AI Foundry
(Web Search tool, perguntas multi-perspectiva estilo STORM) e um Agente Sintetizador que
consolida tudo em um painel de 10 seções — cada uma com grau de suporte calculado em
código (não pelo LLM) a partir das evidências citadas. Relatórios são persistidos como
documento único no Cosmos DB serverless, com histórico consultável e modo offline para
demonstrações. Detalhes completos, decisões técnicas e justificativas em
[`specs/001-radar-tendencias/plan.md`](specs/001-radar-tendencias/plan.md) e
[`docs/architecture.md`](docs/architecture.md).

## Como rodar local

```bash
uv venv --python 3.11 .venv
.venv\Scripts\activate          # Windows; source .venv/bin/activate no Linux/Mac
uv pip install -r requirements-dev.txt

cp .env.example .env            # preencher com endpoint Foundry e Cosmos
az login

python -m streamlit run app/Home.py
# → http://localhost:8501
```

Instruções completas (incluindo modo offline `RADAR_OFFLINE=1`) em
[`specs/001-radar-tendencias/quickstart.md`](specs/001-radar-tendencias/quickstart.md).

Antes de uma demonstração sem depender de rede: exporte relatórios do Cosmos para
disco com `python infra/export_reports.py` e defina `RADAR_OFFLINE=1` no `.env`.

## Como testar

```bash
pytest              # unit + integration, tudo mockado — sem custo, sem credenciais
pytest -m live       # smoke test contra Azure real (exige .env válido; consome tokens/RU)
```

40 testes automatizados cobrem os módulos críticos do pipeline (Princípio V): dedup,
grau de suporte, parsing/validação da saída do Sintetizador, coletores acadêmicos e o
orquestrador completo (fluxo feliz, degradação parcial e total, timeout).

## Estrutura do projeto

```text
app/            Streamlit — UI (Home, Histórico, Evidências)
src/radar/      Pacote instalável (pipeline, agentes, coletores, storage)
tests/          Unit + integração (mockados) e fixtures
infra/          Scripts e documentação de provisionamento Azure
docs/           Arquitetura e avaliação crítica
specs/          Constituição, spec, plano, research e tasks (spec-kit)
```

## Como fazer deploy

Provisionamento completo (Cosmos DB, App Service, Managed Identity, freios de custo) em
[`infra/provision.md`](infra/provision.md). Ambiente de referência já implantado:
resource group `radar-trends`, região `brazilsouth` (mesma do projeto Azure AI Foundry,
para evitar latência cross-region).

## Avaliação crítica

Custos estimados, vieses conhecidos, limitações e evoluções futuras em
[`docs/critical-review.md`](docs/critical-review.md) — inclui o relato honesto do
atrito real de provisionamento (mudanças de região, bloqueios de plataforma) enfrentado
durante o desenvolvimento.

## Contexto do desafio

Este projeto foi desenvolvido para o desafio **SENAI do Futuro — IA** (Radar de
Tendências Tecnológicas). A especificação completa do problema de negócio está em
[`specs/001-radar-tendencias/spec.md`](specs/001-radar-tendencias/spec.md).
