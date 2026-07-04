# Avaliação Crítica — Radar de Tendências Tecnológicas

> Documento vivo exigido pelo Princípio VI da constituição. Atualizado a cada fase.
> Base da seção de avaliação crítica da apresentação à banca.
>
> Última atualização: 2026-07-04 (fase: plan — pós-revisão octo-cloud-architect)

## Custos estimados

Preços verificados em jul/2026, sujeitos a região — substituir por números medidos via
campo `metrics` dos relatórios antes da apresentação.

### Fixo mensal

| Item | Estimativa |
|---|---|
| App Service B1 Linux | ~US$13,14/mês |
| Cosmos DB serverless | < US$1/mês neste volume (~US$0,25/1M RU + ~US$0,25/GB-mês) |
| Foundry Agent Service / Bing grounding | sem custo fixo (por token e por transação) |
| **Total fixo** | **~US$14-15/mês** |

### Por análise

| Item | Cálculo | Estimativa |
|---|---|---|
| GPT-4.1 Agente Coletor | 30-60k tokens in (resultados de busca no contexto) + 4-8k out (US$2/M in, US$8/M out) | US$0,09-0,18 |
| GPT-4.1 Agente Sintetizador | 10-20k in (corpus) + 3-5k out | US$0,05-0,08 |
| Grounding with Bing Search | US$35/1.000 transações; 4-8 tool calls/análise | US$0,14-0,28 |
| Cosmos (escrita ~15-30 RU) | — | < US$0,01 |
| **Total por análise** | | **~US$0,30-0,60** |

Cenário 100 análises/mês: **~US$45-75/mês total**. Alavanca de custo dominante: número
de perguntas multi-perspectiva (cada uma = tool call do Bing + contexto no Coletor) —
por isso fixado em 4 no MVP (R2).

**Freios de abuso** (app público sem auth — R10): Access Restrictions por IP, limite
`MAX_ANALYSES_PER_DAY=10`, budget alert de US$30/mês, TPM baixo no deployment.

## Vieses conhecidos

- **De fonte**: consultorias pagas (Gartner/McKinsey) entram só pelo material público —
  viés para o que essas empresas escolhem divulgar gratuitamente; arXiv enviesa para
  preprints de CS/física (mitigado por OpenAlex, cobertura multidisciplinar).
- **De idioma**: corpus predominantemente em inglês; sinais de mercado brasileiro
  sub-representados (busca cobre pt+en, mas o volume publicado difere).
- **De modelo**: o Sintetizador (GPT-4.1) pode privilegiar narrativas dominantes no
  treinamento. Mitigação estrutural: só afirma com citação; graduação de suporte é
  código determinístico, não autoavaliação do LLM (R8); divergências explicitadas.
- **De recorte do buscador**: o ranking do Bing decide o que o Coletor vê — mitigado
  parcialmente pelas 4 perspectivas STORM e pelas fontes acadêmicas determinísticas.

## Limitações conhecidas (fase de plano)

1. Plataforma de agentes "classic" do Foundry deprecated (retirada 31/03/2027) — spike
   dia 1 valida; migração para nova agents API é evolução declarada (R1).
2. Sem acesso a texto completo pago (paywalls) — evidências baseadas em
   abstracts/sumários/cobertura pública.
3. Patentes só por sinais via busca web — sem API dedicada no MVP.
4. Usuário único, sem auth — controle de acesso por IP allowlist apenas.
5. SC-001 (≤5 min) apertado contra latência do agente com 4 buscas groundadas — medir
   no spike; plano B: 2 runs paralelos (achado 7 da revisão).
6. Análise síncrona in-process no Streamlit — execução não sobrevive a restart do App
   Service (mitigado por doc `running` persistido + retomada manual).

## Evoluções futuras priorizadas

1. Migração para a nova agents API do Foundry / Web Search tool (elimina recurso Bing
   separado).
2. API dedicada de patentes (EPO OPS — cobertura mundial incl. BR, conta gratuita).
3. Easy Auth/Entra ID + multiusuário; Key Vault + RBAC data plane no Cosmos
   (`disableLocalAuth`).
4. Monitoramento contínuo de temas agendado (Azure Functions timer) com diff entre
   execuções.
5. Observabilidade de custo por consulta (Application Insights + metrics do Report).
6. Avaliação de qualidade de evidência por fonte (ranking de confiabilidade).
