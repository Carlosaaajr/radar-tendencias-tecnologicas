# Avaliação Crítica — Radar de Tendências Tecnológicas

> Documento vivo exigido pelo Princípio VI da constituição. Atualizado a cada fase.
> Base da seção de avaliação crítica da apresentação à banca.
>
> Última atualização: 2026-07-04 (provisionamento real — pivot Web Search tool, ver R1)

## Achado real de provisionamento (2026-07-04)

Ao provisionar o projeto Foundry (`omc-cli/omc-ccg-cli`, brazilsouth) para o spike do
dia 1, dois bloqueios reais invalidaram a suposição original de usar GPT-4.1 + Bing
Grounding "classic":

1. **GPT-4.1 e toda a família GPT-4o estão `Deprecating`** para novo deployment nesta
   conta (só GPT-5.x é `GenerallyAvailable`).
2. **O recurso Bing Grounding (SKU G1) não é elegível** nesta assinatura (restrição
   típica de contas PAYG individuais, que exigem Enterprise Agreement/CSP).

Decisão: pivotar para o **Web Search tool** nativo da nova agents API (GA, sem recurso
externo) com deployment dedicado `gpt-5-radar` (gpt-5.4-mini). Isso **elimina o custo de
transação do Bing** das estimativas abaixo e remove uma dependência de provisionamento —
achado positivo em meio ao replanejamento. Detalhes em research.md R1.

## Spike T006 — validado (2026-07-04)

Rodado contra o projeto real (`omc-cli/omc-ccg-cli`) via
`AIProjectClient.get_openai_client()` + `responses.create(model="gpt-5-radar",
tools=[{"type": "web_search"}])`:

- **Latência**: 30,3s para 1 pergunta com busca web (`item.type=web_search_call` +
  `message`). Para as 4 perguntas do R2, rodar concorrente (`asyncio.gather`) é
  obrigatório para caber em SC-001 (≤5 min) — sequencial ultrapassaria 2 min só na coleta
  de mercado.
- **Citações**: 13 `url_citation` retornadas para 1 pergunta (com duplicatas — a
  deduplicação do FR-007 absorve isso), incluindo fontes reais como NVIDIA, Siemens,
  Intel, Accenture e Deloitte — cobre exatamente os tipos de fonte que o desafio pede.
- **Formato da anotação**: `{type, url, title, start_index, end_index}` — os índices
  permitem extrair o snippet como a janela de texto ao redor da citação no
  `output_text`/`content` da mensagem (usado em `collector_agent.py`, T023).
- Resultado bruto salvo em `infra/spike_result.json`.

## Deploy real — atrito de provisionamento (2026-07-04)

Ao provisionar Cosmos DB + App Service, dois achados adicionais de infraestrutura real:

1. **Região `eastus` sem capacidade para contas Cosmos DB novas** no momento do deploy
   (`ServiceUnavailable`, mesmo com `isZoneRedundant=False`) — erro genuíno da Azure, não
   do comando. Resolvido migrando Cosmos DB + App Service para **`brazilsouth`**, a mesma
   região do projeto Foundry — elimina também a latência cross-region entre o App Service
   e os agentes.
2. **Conexões HTTPS de longa duração instáveis** durante `az cosmosdb create`/`az webapp
   create` (connection reset em operações longas). Mitigado rodando os comandos em
   background e verificando o estado via chamadas curtas (`az ... show`) em vez de manter
   o poll síncrono do CLI.

Aprendizado para a apresentação: capacidade regional de serviços gerenciados **não é
garantida nem estável** — o plano de arquitetura deve sempre ter uma região alternativa
pronta (aqui, colocalizar com o Foundry em `brazilsouth` resolveu dois problemas de uma vez).

## Custos estimados

Preços verificados em jul/2026, sujeitos a região — substituir por números medidos via
campo `metrics` dos relatórios antes da apresentação.

### Fixo mensal

| Item | Estimativa |
|---|---|
| App Service B1 Linux | ~US$13,14/mês |
| Cosmos DB serverless | < US$1/mês neste volume (~US$0,25/1M RU + ~US$0,25/GB-mês) |
| Foundry Agent Service / Web Search tool | sem custo fixo (por token e por chamada de ferramenta) |
| **Total fixo** | **~US$14-15/mês** |

### Por análise

| Item | Cálculo | Estimativa |
|---|---|---|
| gpt-5-radar (Agente Coletor) | 30-60k tokens in (resultados de busca no contexto) + 4-8k out — preço a confirmar no smoke test (T036), ordem de grandeza próxima do GPT-4.1 | US$0,09-0,18 (verificar) |
| gpt-5-radar (Agente Sintetizador) | 10-20k in (corpus) + 3-5k out | US$0,05-0,08 (verificar) |
| Web Search tool | cobrança por chamada de ferramenta — preço a confirmar no smoke test (sem tarifário de "transação Bing" separado neste caminho) | verificar |
| Cosmos (escrita ~15-30 RU) | — | < US$0,01 |
| **Total por análise** | | **a confirmar em T036 — ordem de grandeza US$0,20-0,50** |

Cenário 100 análises/mês: estimativa preliminar **~US$30-60/mês total** (a confirmar).
Alavanca de custo dominante: número de perguntas multi-perspectiva (cada uma = chamada
de ferramenta + contexto no Coletor) — por isso fixado em 4 no MVP (R2). **Ação
obrigatória**: substituir esta tabela por números medidos no smoke test de produção
(T036), já que o tarifário de `gpt-5.4-mini` + Web Search tool não estava confirmado
nesta fase de planejamento.

**Freios de abuso** (app público sem auth — R10): Access Restrictions por IP, limite
`MAX_ANALYSES_PER_DAY=10`, budget alert de US$30/mês, TPM baixo no deployment.

## Vieses conhecidos

- **De fonte**: consultorias pagas (Gartner/McKinsey) entram só pelo material público —
  viés para o que essas empresas escolhem divulgar gratuitamente; arXiv enviesa para
  preprints de CS/física (mitigado por OpenAlex, cobertura multidisciplinar).
- **De idioma**: corpus predominantemente em inglês; sinais de mercado brasileiro
  sub-representados (busca cobre pt+en, mas o volume publicado difere).
- **De modelo**: o Sintetizador (`gpt-5-radar`) pode privilegiar narrativas dominantes no
  treinamento. Mitigação estrutural: só afirma com citação; graduação de suporte é
  código determinístico, não autoavaliação do LLM (R8); divergências explicitadas.
- **De recorte do buscador**: o ranking do provedor de busca por trás do Web Search
  tool decide o que o Coletor vê — mitigado parcialmente pelas 4 perspectivas STORM e
  pelas fontes acadêmicas determinísticas.

## Limitações conhecidas (fase de plano)

1. GPT-4.1/GPT-4o não são mais implantáveis nesta conta (deprecating) e o recurso Bing
   Grounding "classic" não é elegível nesta assinatura — pipeline usa Web Search tool +
   `gpt-5-radar` (R1); tarifário ainda não confirmado (ver smoke test T036).
2. Sem acesso a texto completo pago (paywalls) — evidências baseadas em
   abstracts/sumários/cobertura pública.
3. Patentes só por sinais via busca web — sem API dedicada no MVP.
4. Usuário único, sem auth — controle de acesso por IP allowlist apenas.
5. SC-001 (≤5 min) apertado contra latência do agente com 4 buscas web — medir no
   spike; plano B: 2 runs paralelos (achado 7 da revisão de arquitetura).
6. Análise síncrona in-process no Streamlit — execução não sobrevive a restart do App
   Service (mitigado por doc `running` persistido + retomada manual).
7. Deployment `gpt-5-radar` tem capacidade reservada baixa (10 TPM-equivalente) para
   isolar do restante da conta `omc-cli` (compartilhada com outras ferramentas) —
   suficiente para demo, pode gargalar sob uso concorrente real.

## Code review (octo-code-reviewer, 2026-07-04) — achados e status

Revisão obrigatória da constituição (T039) sobre todo o pipeline. Veredito: **aprovado
com ressalvas**. 3 achados ALTO corrigidos antes da apresentação (bugs reais de
resiliência que contradiziam o Princípio IV/FR-012):

- **Corrigido**: `OpenAlexCollector` derrubava a coleta inteira quando um registro
  vinha com `primary_location.source=null` (comum em preprints) — `AttributeError` não
  capturado escapava do collector. Agora o parsing inteiro está sob try/except e trata
  `source` ausente/nulo com segurança. Teste de regressão adicionado.
- **Corrigido**: a coleta acadêmica (`asyncio.gather` de arXiv + OpenAlex) propagava
  qualquer exceção crua em vez de degradar a fonte — combinado com o bug acima, uma
  falha de parsing abortava a análise inteira em vez de completar com aviso. Agora usa
  `return_exceptions=True` e trata exceção como fonte degradada. Teste de regressão
  adicionado.
- **Corrigido**: `synthesize()` chamava o cliente OpenAI de forma síncrona e bloqueante
  dentro de uma função `async`, sem `asyncio.to_thread` nem `timeout` — o
  `asyncio.wait_for` do orquestrador não conseguia de fato interromper uma chamada
  pendurada, podendo congelar a demo inteira (processo single-thread). Corrigido para
  rodar em thread com timeout efetivo.
- **Corrigido**: relatórios com falha não tratada ficavam com `status=running` e
  apareciam como "✅ Completo" no histórico. Adicionado estado visual explícito
  "⏳ Incompleto".

**Não corrigidos nesta fase** (severidade média/baixa, custo-benefício menor para o
prazo — registrados como limitação/evolução):
- Sem validação de que as 10 seções obrigatórias foram todas geradas pelo Sintetizador
  (FR-004); seção ausente falha silenciosamente em vez de gerar aviso explícito.
- `list_summaries` desserializa o relatório completo para montar o resumo do histórico
  — aceitável no volume do MVP, mas não escala; persistir `support_overview`
  pré-computado resolveria.
- Cobertura de teste da função `synthesize()` (retry/parsing de streaming) é indireta,
  via `parse_synthesis_output`; o caminho de timeout do LLM não tem teste dedicado.
- Tema do usuário entra sem sanitização nos prompts (risco de prompt injection) —
  mitigado estruturalmente pela graduação determinística em código (LLM não consegue
  fabricar grau de suporte alto só por manipular o prompt), mas vale mencionar como
  limitação conhecida na arguição.

## Evoluções futuras priorizadas

1. Reavaliar migração de assinatura (Enterprise Agreement/CSP) caso o Bing Grounding
   "classic" com citações mais ricas seja desejado no futuro.
2. API dedicada de patentes (EPO OPS — cobertura mundial incl. BR, conta gratuita).
3. Easy Auth/Entra ID + multiusuário; Key Vault + RBAC data plane no Cosmos
   (`disableLocalAuth`).
4. Monitoramento contínuo de temas agendado (Azure Functions timer) com diff entre
   execuções.
5. Observabilidade de custo por consulta (Application Insights + metrics do Report).
6. Avaliação de qualidade de evidência por fonte (ranking de confiabilidade).
