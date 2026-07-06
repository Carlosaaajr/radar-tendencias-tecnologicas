# Research: Radar de Tendências Tecnológicas

**Date**: 2026-07-03 | **Feature**: 001-radar-tendencias

Todas as incertezas do Technical Context foram resolvidas. Decisões abaixo no formato
Decision / Rationale / Alternatives.

## R1. Agentes de IA — Azure AI Foundry Agent Service

- **Decision** (revisada em 2026-07-04 após provisionamento real — ver "Achados do
  provisionamento" abaixo): Dois agentes criados programaticamente via SDK Python
  `azure-ai-projects` (nova agents API), autenticação via `DefaultAzureCredential`:
  - **Agente Coletor**: modelo `gpt-5-radar` (deployment dedicado de `gpt-5.4-mini`,
    GlobalStandard, conta `omc-cli`) com a ferramenta nativa **Web Search tool** (GA,
    sem recurso Azure separado);
  - **Agente Sintetizador**: mesmo modelo, sem ferramentas (recebe corpus, devolve JSON
    do painel), saída estruturada.
- **Rationale**: Requisito do usuário (agentes no Foundry). Web Search tool é nativo da
  nova agents API, devolve citações de URL (alimenta o Princípio I) e não depende de um
  recurso `Microsoft.Bing/accounts` pago à parte — elimina o bloqueio de elegibilidade de
  SKU encontrado nesta assinatura. Docs: [Web search tool](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/web-search).
- **Achados do provisionamento real (2026-07-04, projeto `omc-cli/omc-ccg-cli`,
  brazilsouth, resource group `ai-models-resource`)** — invalidam a suposição original
  de usar GPT-4.1 e motivam esta revisão:
  1. **GPT-4.1 (2025-04-14) e toda a família GPT-4o estão `Deprecating`** nesta conta —
     `az cognitiveservices account deployment create` rejeita novos deployments desses
     modelos (`ServiceModelDeprecating`). Só a família **GPT-5.x está `GenerallyAvailable`**
     para novo deployment (confirmado via `az cognitiveservices account list-models`,
     campo `lifecycleStatus`/`deprecation.inference`).
  2. **O recurso `Microsoft.Bing/accounts` (SKU `G1`, Grounding with Bing Search
     "classic") não é elegível nesta assinatura** (`SkuNotEligible` — restrição típica de
     assinaturas PAYG individuais, que normalmente exigem Enterprise Agreement/CSP para
     esse recurso). Isso fecha de vez o caminho `BingGroundingTool`/classic para este
     ambiente, independente da questão de compatibilidade de modelo.
  3. Deployment dedicado `gpt-5-radar` (`gpt-5.4-mini`, versão `2026-03-17`, GA,
     GlobalStandard, capacidade 10) criado com sucesso — capabilities incluem
     `agentsV2: true`, confirmando suporte à nova agents API.
  - **Consequência**: o "spike do dia 1" (antes T006) deixa de ser uma validação de
    caminho classic-vs-novo — o caminho classic está descartado por bloqueio real de
    assinatura. O spike agora valida diretamente o Web Search tool com `gpt-5-radar` na
    nova agents API (formato das citações + latência).
  - Requer rede normal (sem VPN/Private Endpoint) — ok para MVP.
  - **Autenticação em produção**: o Foundry exige Entra ID no project endpoint (sem key
    auth). `DefaultAzureCredential` só funciona no App Service com **Managed Identity
    system-assigned + role "Azure AI User"** no projeto Foundry — incluído no
    provisionamento (quickstart).
- **Alternatives considered**:
  - *BingGroundingTool* (classic ou nova API) — rejeitado: bloqueio real de SKU de
    assinatura (achado 2 acima), não apenas preferência.
  - Azure OpenAI direto (sem Agent Service) + SerpAPI/Tavily — rejeitado: viola o
    requisito de agentes no Foundry e adiciona fornecedor externo.
  - Semantic Kernel/AutoGen para orquestração — rejeitado: camada extra sem ganho no
    MVP (Princípio II); orquestração é um pipeline sequencial simples em Python puro.

## R2. Técnica multi-perspectiva (inspirada no STORM)

- **Decision**: O orquestrador instrui o Agente Coletor a gerar **4 perguntas** sobre o
  tema (uma por perspectiva fixa: técnica, econômica/mercado, industrial/adoção,
  regulatória/riscos) e responder cada uma com busca web nativa; cada resposta traz
  citações (via `responses.create(tools=[{"type": "web_search"}])`). As 4 chamadas
  **MUST rodar concorrentes** (`asyncio.gather`), nunca sequenciais — o spike T006 mediu
  30,3s para 1 pergunta; sequencial ultrapassaria 2 min só nesta etapa, inviabilizando
  SC-001 (≤5 min). As perguntas e respostas viram evidências tipadas.
- **Rationale**: Reproduz o núcleo do STORM (perspective-guided question asking) sem
  importar o framework (dspy/litellm), que conflitaria com o Agent Service e o prazo
  (Princípio II). Diversifica evidências e é argumento metodológico forte para a banca —
  a técnica não foi inventada pelo projeto, vem de pesquisa publicada e revisada por
  pares do **Stanford OVAL (Open Virtual Assistant Lab)**:
  - Shao, Y., Jiang, Y., Kanell, T. A., Xu, P., Khattab, O., & Lam, M. S. (2024).
    *Assisting in Writing Wikipedia-like Articles From Scratch with Large Language
    Models*. NAACL 2024. [arXiv:2402.14207](https://arxiv.org/abs/2402.14207)
    — origem do "perspective-guided question asking" (STORM) que este projeto adapta.
  - Jiang, Y., Shao, Y., Ma, D., Semnani, S., & Lam, M. (2024). *Into the Unknown
    Unknowns: Engaged Human Learning through Participation in Language Model Agent
    Conversations*. EMNLP 2024. [arXiv:2408.15232](https://arxiv.org/abs/2408.15232)
    — Co-STORM (discurso colaborativo entre agentes com papéis distintos + mapa mental
    dinâmico); **não implementado** neste projeto, registrado como evolução futura
    (ver seção de evoluções em `docs/critical-review.md`).
- **Alternatives considered**: usar o pacote `knowledge-storm` completo — rejeitado
  (pipeline próprio incompatível com Foundry Agent Service; dependência pesada);
  busca única sem perspectivas — rejeitado (evidências homogêneas, grau de suporte pobre).
- **Escopo do que foi de fato adaptado (para não superestimar na arguição)**: só o
  princípio de gerar perguntas fixas sob perspectivas diferentes antes de buscar. **Não**
  reproduzido: simulação de conversa multi-agente entre personas, refinamento iterativo
  de perguntas a partir de respostas anteriores, geração de outline, ou o protocolo
  colaborativo do Co-STORM (moderador, mapa mental). Aqui as 4 perguntas são templates
  fixos e rodam em paralelo, não em diálogo sequencial.

## R3. Fontes acadêmicas determinísticas

- **Decision**: `arXiv API` (XML/Atom, sem chave) + `OpenAlex` (JSON, sem chave,
  `mailto` recomendado) chamadas diretamente via `httpx` no orquestrador Python.
  Semantic Scholar fica como fallback documentado (rate limit sem chave é restritivo).
- **Rationale**: Cobrem "artigos científicos/Google Scholar" do desafio com metadados
  estruturados (título, autores, data, DOI, contagem de citações → insumo direto do grau
  de suporte). Sem fricção de credencial. OpenAlex indexa também Nature/ScienceDirect
  (metadados e abstracts, não texto completo — suficiente para evidências).
- **Alternatives considered**: Google Scholar scraping — rejeitado (sem API, bloqueio);
  Semantic Scholar como primário — rejeitado (429 frequente sem chave); apenas arXiv —
  rejeitado (viés para preprints de CS/física).

## R4. UI e hospedagem

- **Decision**: Streamlit (multipage) no Azure App Service Linux plano B1, deploy via
  `az webapp up`/GitHub zip deploy, startup command:
  `python -m streamlit run app/Home.py --server.port 8000 --server.address 0.0.0.0 --server.headless true`.
  **Always On habilitado** (evita cold start de 30-90 s na demo). Configuração de proxy
  versionada em `.streamlit/config.toml` (CORS/XSRF se necessário). O documento
  `status=running` é persistido no início do pipeline e atualizado ao fim — rerun ou
  queda de WebSocket não perde a execução; `st.session_state` guarda flag para não
  reiniciar o pipeline em rerun acidental.
  **Achado do deploy real (2026-07-04)**: `az webapp create` cria o App Service com
  `webSocketsEnabled=false` por padrão — **obrigatório** habilitar explicitamente
  (`az webapp config set --web-sockets-enabled true`), pois o Streamlit depende de
  WebSocket para as atualizações de UI; sem isso, o app carrega mas trava sem
  atualizar. Adicionado a `infra/provision.md`.
- **Rationale**: Decisão do usuário (Python full + App Service). Startup command é o
  padrão documentado para Streamlit no App Service Linux
  ([guia azureossd](https://azureossd.github.io/2024/04/18/Deploying-a-Python-Streamlit-app-to-App-Service-Linux/),
  [Tech Community](https://techcommunity.microsoft.com/blog/appsonazureblog/deploy-streamlit-on-azure-web-app/4276108)).
  Streamlit usa Tornado — não usar Gunicorn.
- **Alternatives considered**: Container Apps — rejeitado pelo usuário (App Service
  escolhido); Docker custom — desnecessário (runtime Python nativo do App Service basta).

## R5. Persistência

- **Decision**: Azure Cosmos DB serverless (API NoSQL), database `radar`, containers:
  `reports` (partition key `/theme_slug`) e `evidence` embutida no documento do
  relatório (não em container separado). SDK `azure-cosmos`.
- **Rationale**: Relatório é um agregado autocontido lido sempre inteiro (painel +
  evidências + graus de suporte) → documento único elimina joins e mantém leitura do
  histórico < 5 s (SC-003). Serverless: custo por RU consumida, ~centavos no volume do
  MVP (Princípio de custo documentado).
- **Alternatives considered**: container separado de evidências — rejeitado (leitura
  sempre conjunta; documento < 2 MB no volume esperado); Blob Storage JSON — rejeitado
  (sem consulta por campo para o histórico); Table Storage — rejeitado (JSON aninhado
  ruim).

## R6. Segredos e configuração

- **Decision**: Variáveis de ambiente (App Settings no App Service) no MVP:
  `PROJECT_ENDPOINT`, `MODEL_DEPLOYMENT_NAME` (= `gpt-5-radar`), `COSMOS_ENDPOINT`,
  `COSMOS_KEY`. Localmente via `.env` (python-dotenv), `.env` no `.gitignore`. Sem
  variável de conexão Bing — Web Search tool não depende de recurso/conexão externa.
  Key Vault + Managed Identity documentados como hardening de produção (avaliação
  crítica / evolução futura).
- **Rationale**: Princípio III exige env vars ou Key Vault; App Settings são cifradas em
  repouso e suficientes para MVP de 1 semana. `DefaultAzureCredential` já prepara a
  transição para Managed Identity sem mudança de código no acesso ao Foundry.
- **Alternatives considered**: Key Vault desde o dia 1 — adiado (setup extra sem ganho
  na demo; anotado como evolução).

## R7. Testes

- **Decision**: `pytest` + `respx` (mock de HTTP para arXiv/OpenAlex) + fixtures JSON.
  Cobertura obrigatória nos módulos: normalização/deduplicação de evidências, cálculo de
  grau de suporte, parsing das respostas dos agentes (JSON schema), fallbacks de coleta.
  Smoke test opcional end-to-end marcado `@pytest.mark.live` (exige credenciais).
- **Rationale**: Princípio V exige testes nos módulos críticos; mocks mantêm a suíte
  executável em CI sem credenciais/custos.
- **Alternatives considered**: VCR/cassettes — rejeitado (respostas de LLM não são
  determinísticas; fixtures explícitas são mais claras).

## R8. Grau de suporte (algoritmo)

- **Decision**: Por seção do painel: contagem de evidências citadas, nº de tipos de
  fonte distintos (científica, mercado/consultoria, notícia, corporativa, patente) e
  flag de divergência (apontada pelo Sintetizador quando fontes conflitam). Classificação
  exibida: **Alto** (≥4 evidências E ≥2 tipos), **Médio** (2-3 evidências, OU ≥4
  evidências com menos de 2 tipos), **Baixo** (1), **Inferência** (0 — marcada, sem
  grau). Regra total: toda combinação (contagem, tipos) tem classificação definida.
  Computado deterministicamente no orquestrador a partir das citações, não pelo LLM.
- **Rationale**: FR-005/FR-006/SC-002. Cálculo determinístico é testável e auditável —
  o LLM apenas cita; quem gradua é código (defesa forte na arguição sobre alucinação).
- **Alternatives considered**: LLM autoavaliar confiança — rejeitado (não auditável,
  viés de superconfiança).

## R9. Resiliência de demo — modo offline local (ajuste da revisão de arquitetura)

- **Decision**: Flag `RADAR_OFFLINE=1` troca o `ReportRepository` (Cosmos) por
  `LocalReportRepository` que lê/grava os mesmos documentos JSON em `data/reports/` no
  disco. Antes da apresentação, 2-3 relatórios são exportados do Cosmos para o disco;
  o Streamlit roda no notebook do apresentador se a rede do local cair. Último recurso:
  export HTML/PDF estático dos relatórios.
- **Rationale**: O cache no Cosmos não satisfaz o Princípio IV se não houver rede no
  local — app e banco estão no Azure. Como o repositório é uma interface e a separação
  `app/` vs `src/radar/` já existe, o custo é ~1 h (achado ALTO da revisão).
- **Alternatives considered**: confiar só no Cosmos — rejeitado (furo apontado na
  revisão); demo gravada em vídeo — mantida como redundância de apresentação, não
  substitui interatividade.

## R10. Controle de abuso de custo (ajuste da revisão de arquitetura)

- **Decision**: Três freios no MVP: (1) **Access Restrictions** no App Service
  (allowlist de IP; liberado apenas durante a demo); (2) limite de análises/dia no
  orquestrador (default 10, configurável via `MAX_ANALYSES_PER_DAY`), verificado antes
  de iniciar o pipeline; (3) **Azure Budget alert** (~US$30/mês, criado manualmente no
  portal — `az consumption budget create` tem bug reproduzível nesta API preview) + TPM
  moderado no deployment `gpt-5-radar` (capacidade **50**, isolado dos demais usos da
  conta — ver achado do smoke test abaixo).
- **Rationale**: App público sem auth executando pipeline pago (~US$0,30-0,60/análise)
  em domínio `*.azurewebsites.net` varrível por bots = risco real de custo (achado ALTO).
  Usuário único sem auth continua como decisão de produto; os freios custam horas.
- **Achado real do smoke test (T036, 2026-07-05)**: a capacidade inicial de 10 unidades
  causou `RateLimitError (429)` real durante a síntese de uma análise legítima (4
  buscas web concorrentes + 1 chamada de síntese sobre o corpus consolidado excedem 10
  unidades). Aumentada para **50** — ainda um teto explícito e modesto (não
  "ilimitado"), suficiente para uma análise completa sem risco de rate limit em uso
  normal. Esse mesmo evento revelou um gap de resiliência real: o orquestrador só
  tratava `TimeoutError`/`SynthesisError` na etapa de síntese, não erros de API do SDK
  (`openai.RateLimitError`) — corrigido para tratar qualquer exceção da síntese como
  `status=partial` (Princípio IV).
- **Alternatives considered**: Easy Auth (Entra built-in) — plano B de custo zero em
  código, mas exige validar interferência com WebSocket do Streamlit; adiado para
  evolução futura junto com multiusuário.

## Sources

- [Use Grounding with Bing Search tools with the agents API — Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/bing-tools)
- [How to use Grounding with Bing Search in Foundry Agent Service — Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/bing-grounding?view=foundry-classic)
- [Deploying a Python Streamlit app to App Service Linux — azureossd](https://azureossd.github.io/2024/04/18/Deploying-a-Python-Streamlit-app-to-App-Service-Linux/)
- [Deploy Streamlit on Azure Web App — Microsoft Tech Community](https://techcommunity.microsoft.com/blog/appsonazureblog/deploy-streamlit-on-azure-web-app/4276108)
- [stanford-oval/storm — técnica multi-perspectiva](https://github.com/stanford-oval/storm)
