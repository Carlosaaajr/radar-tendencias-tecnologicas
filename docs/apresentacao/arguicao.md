# Guia de Arguição — Radar de Tendências Tecnológicas

> Material de apoio para os 10 minutos de arguição da banca (SENAI do Futuro — IA).
> Organizado pelos 5 critérios de avaliação do desafio. Respostas curtas e diretas —
> use como cola mental, não leia ao vivo.

## Como abrir a arguição (se a banca não emplacar logo)

"Antes das perguntas, um resumo em uma frase: o sistema não tenta ser mais esperto que
o LLM — ele desconfia dele. Todo grau de confiança que vocês viram no painel foi
calculado em código, a partir de citações reais, nunca pelo próprio modelo. Essa é a
decisão central do projeto."

---

## 1. Entendimento do problema

**P: Por que um painel executivo e não só um chat com o LLM?**
R: Diretoria não quer conversar com um chatbot, quer um documento que possa citar em
reunião. O desafio pede explicitamente "grau de suporte encontrado nas fontes" — isso
não existe em um chat comum, exige estrutura: seções fixas, evidências anexadas, grau
calculado. É a diferença entre "pergunte ao ChatGPT" e uma ferramenta de decisão.

**P: Por que essas 10 seções especificamente?**
R: Vieram direto do enunciado do desafio (Etapa 3): definição, maturidade, aplicações,
setores, players, investimentos, adoção, oportunidades, riscos, perspectivas. Não
inventamos taxonomia — traduzimos literalmente o que a diretoria pediu.

**P: Como o sistema lida com um tema ambíguo, tipo "IA"?**
R: Segue com a interpretação mais provável e expõe o recorte adotado no painel
(`scope_note`) — nunca finge que não é ambíguo. Documentado como edge case na spec.

**P: Por que só 2 exemplos testados (Edge AI, Robôs Humanoides)?**
R: São os 2 exemplos do próprio enunciado do desafio — usamos exatamente eles para o
smoke test final em produção, sem escolher a dedo temas favoráveis.

---

## 2. Arquitetura da solução

**P: Por que Streamlit e não React/Next.js?**
R: Decisão de prazo (1 semana) e de time único. Streamlit entrega UI funcional em
Python puro sem separar front/back — a spec é agnóstica de tecnologia de propósito
(documentamos isso: trocar a UI não muda um requisito sequer). Trade-off consciente,
não desconhecimento.

**P: Por que Cosmos DB e não Postgres/Blob Storage?**
R: O relatório é um agregado que sempre se lê inteiro (painel + evidências + graus de
suporte) — documento único elimina joins e mantém reabertura do histórico abaixo de 5s
(SC-003). Serverless: custo por operação, não por instância ociosa.

**P: Por que agentes no Azure AI Foundry e não só chamar a API do modelo direto?**
R: Era requisito do desafio ("agentes implementados no Azure AI Foundry Agent Service").
Além disso, o Foundry dá o Web Search tool nativo com citações estruturadas
(`url_citation` com posição no texto) — é isso que alimenta a rastreabilidade sem
reinventar parsing de busca.

**P: Explique a técnica "multi-perspectiva" — é STORM de verdade?**
R: Inspirada no núcleo do STORM (Stanford): gerar perguntas sob perspectivas diferentes
antes de responder, para diversificar evidências. Não importamos o framework STORM
completo (ele não é compatível com o Agent Service e adicionaria peso desnecessário) —
reproduzimos o princípio com 4 perguntas fixas (técnica, econômica, industrial,
regulatória) rodando **concorrentes**, porque medimos ~30s por pergunta no spike e
sequencial estouraria o limite de 5 minutos (SC-001).

**P: Por que Web Search tool e não Bing Grounding, que estava no plano original?**
R: Achado real de provisionamento, não escolha de conforto: GPT-4.1/4o estavam em
depreciação para novo deployment nesta conta, e o recurso Bing Grounding (SKU G1) não
era elegível na assinatura (exige Enterprise Agreement). Pivotamos para o Web Search
tool nativo da nova agents API — GA, sem recurso externo, e documentamos a decisão com
o achado que a motivou (research.md R1). É exatamente o tipo de decisão de arquitetura
que se testa contra a realidade, não só no papel.

**P: Por que a região Brazil South e não East US?**
R: Outro achado real: East US estava sem capacidade da Azure para novas contas Cosmos
DB no momento do deploy (erro genuíno do provedor). Brazil South resolveu dois
problemas de uma vez: capacidade disponível e colocalização com o Foundry (elimina
latência cross-region).

**P: O sistema escala para múltiplos usuários?**
R: Não no MVP — é decisão consciente de escopo (usuário único, sem auth), documentada
como evolução futura. A separação `app/` (UI) vs `src/radar/` (pipeline) já permite
extrair uma API depois sem reescrever a lógica.

---

## 3. Qualidade de implementação

**P: Como vocês garantem que o LLM não está alucinando o grau de suporte?**
R: Ele não decide o grau — o Sintetizador só pode citar `evidence_id`; um módulo de
código puro (`grading.py`) conta quantas evidências e quantos tipos de fonte sustentam
cada seção e classifica deterministicamente (Alto/Médio/Baixo/Inferência). Se o LLM cita
um id que não existe no corpus, o código rebaixa a seção para "inferência"
automaticamente. É auditável e testado — 7 testes unitários só para essa regra.

**P: Quantos testes tem o projeto? Cobrem o quê?**
R: 43 testes automatizados (unitários + integração), mais um smoke test real contra
produção. Cobrem os módulos críticos: deduplicação, graduação de suporte, parsing da
saída do LLM, coletores (com mocks de API), e o orquestrador completo — incluindo
cenários de falha (fonte degradada, timeout, erro de API).

**P: O código passou por revisão? O que apareceu?**
R: Sim, revisão dedicada (agente de code review) antes da apresentação. Achou 3 bugs
reais de resiliência — por exemplo, um erro de parsing em um registro do OpenAlex que
derrubava a coleta inteira em vez de degradar. Todos corrigidos com testes de
regressão. Depois, o smoke test real contra produção achou mais 3 bugs que só
aparecem contra APIs reais (ex.: arXiv migrou para HTTPS e o redirect não era seguido).
Isso é normal — o valor está em ter processo para achar e corrigir, não em fingir zero bugs.

**P: Por que Streamlit e Cosmos e não containers/Kubernetes?**
R: Princípio de simplicidade orientado a prazo da própria constituição do projeto:
complexidade que não se demonstra em 20 minutos é custo sem retorno. App Service B1 é
suficiente para 1 usuário.

---

## 4. Avaliação crítica (a parte que a banca mais valoriza)

**P: Quanto custa rodar isso?**
R: Fixo: ~US$14-15/mês (App Service B1 + Cosmos serverless). Por análise: estimativa de
US$0,20-0,50 (tokens do modelo + chamadas de busca) — número exato pendente de
confirmação via Azure Cost Management, documentado honestamente como estimativa, não
número inventado.

**P: Quais os vieses que vocês identificaram?**
R: Quatro, documentados: (1) viés de fonte — consultorias pagas só aparecem pelo
material público que elas escolhem divulgar; (2) viés de idioma — corpus
predominantemente em inglês; (3) viés de modelo — o Sintetizador pode privilegiar
narrativas dominantes do treinamento, mitigado por exigir citação; (4) viés de
buscador — o ranking do Web Search decide o que o Coletor vê, mitigado parcialmente
pelas 4 perspectivas.

**P: Qual a maior limitação hoje?**
R: Patentes são cobertas só por sinais via busca web, sem API dedicada (EPO OPS
avaliada e descartada pelo prazo — documentado com o motivo). E o app roda em processo
único: se o App Service reiniciar no meio de uma análise, ela fica órfã (mitigado por
marcar o relatório como "incompleto" no histórico, não como "completo").

**P: O sistema é seguro? Alguém pode manipular o resultado enviando um tema malicioso?**
R: Tema do usuário entra sem sanitização no prompt — risco real de prompt injection,
documentado. Mas a mitigação estrutural importa mais que a sanitização de texto: mesmo
que o prompt seja manipulado, o grau de suporte nunca é calculado pelo LLM, então não
dá para "convencer" o sistema a mostrar grau Alto sem evidências reais no corpus.

**P: O que vocês fariam diferente com mais tempo?**
R: Popular o campo de métricas (tokens/custo real por etapa, hoje vazio — gap
documentado), validar que as 10 seções sempre vêm completas do Sintetizador (hoje falha
silenciosamente se faltar uma), e Key Vault + Managed Identity com RBAC de dados no
Cosmos em vez de chave primária.

---

## 5. Evoluções futuras (perguntas "e se...")

**P: E se quisessem monitorar um tema continuamente, não só sob demanda?**
R: Evolução priorizada e documentada: Azure Functions com timer, comparando execuções
ao longo do tempo (diff de sinais de adoção, por exemplo).

**P: E para múltiplas equipes usarem ao mesmo tempo?**
R: Easy Auth/Entra ID + multiusuário — adiado por escopo, não por dificuldade técnica;
a arquitetura já separa UI de pipeline para isso.

**P: Pensaram em patentes de verdade?**
R: Sim — avaliamos a EPO OPS (cobertura mundial, conta gratuita) e descartamos pelo
prazo de 1 semana, não por desconhecimento. Está na lista de evolução com a
justificativa registrada.

---

## Números para ter na ponta da língua

| Métrica | Valor |
|---|---|
| Seções obrigatórias no painel | 10 |
| User stories da spec | 3 (painel, histórico, evidências) |
| Requisitos funcionais | 15 (FR-001 a FR-015) |
| Critérios de sucesso mensuráveis | 7 (SC-001 a SC-007) |
| Testes automatizados | 43 |
| Perspectivas de busca concorrentes | 4 (técnica, econômica, industrial, regulatória) |
| Smoke test — Edge AI | 123s, 53 evidências, 4 tipos de fonte, 10/10 seções |
| Smoke test — Robôs Humanoides | 37s, 44 evidências, 3 tipos de fonte, 10/10 seções |
| Bugs reais corrigidos (code review + smoke test) | 6 |
| Custo fixo mensal estimado | ~US$14-15 |
| Custo por análise estimado | ~US$0,20-0,50 |

## Se travar em alguma pergunta

Frase de segurança: "Essa é uma limitação que documentamos conscientemente em
`docs/critical-review.md` — preferimos declarar o que não resolvemos a fingir que não
existe." Isso converte "não sei" em prova de avaliação crítica (critério da banca).
