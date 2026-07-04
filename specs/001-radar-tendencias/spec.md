# Feature Specification: Radar de Tendências Tecnológicas

**Feature Branch**: `001-radar-tendencias`

**Created**: 2026-07-03

**Status**: Draft

**Input**: User description: "Radar de Tendências Tecnológicas — plataforma web que recebe do usuário um tema (tendência, tecnologia ou conceito, ex.: 'Edge AI', 'Robôs Humanoides para Indústria') e gera um painel executivo baseado em evidências coletadas na internet, em 3 etapas (definição do tema, coleta automatizada em fontes públicas confiáveis, consolidação em painel estruturado com grau de suporte e referências verificáveis), com histórico persistido e modo cache para demonstração."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar painel executivo a partir de um tema (Priority: P1)

Um analista ou diretor informa um tema de interesse (ex.: "Edge AI") e recebe um painel
executivo estruturado contendo: definição do tema, nível de maturidade, principais
aplicações, setores impactados, empresas e instituições relevantes, investimentos e
movimentos de mercado, sinais de adoção, oportunidades, desafios/riscos e perspectivas
futuras. Cada seção exibe o grau de suporte encontrado nas evidências (quantidade de
fontes, diversidade de tipos, convergência/divergência) e referências verificáveis
(título, origem, endereço e data).

**Why this priority**: É o objetivo central do desafio — sem esta jornada não existe
produto. Sozinha, já entrega o valor prometido: transformar pesquisa manual dispersa em
conhecimento estruturado e acionável.

**Independent Test**: Informar um tema conhecido (ex.: "Edge AI") e verificar que o
painel é gerado com todas as seções obrigatórias preenchidas, cada uma com referências
clicáveis e indicador de grau de suporte.

**Acceptance Scenarios**:

1. **Given** a plataforma disponível, **When** o usuário informa o tema "Edge AI" e
   solicita a análise, **Then** o sistema apresenta um painel com as 10 seções
   obrigatórias, cada uma com pelo menos uma referência verificável (título, fonte, URL
   e data quando disponível).
2. **Given** um painel gerado, **When** o usuário examina qualquer seção, **Then**
   visualiza o grau de suporte da seção (quantidade e tipos de fontes que a sustentam)
   e consegue distinguir afirmações sustentadas por evidências de inferências analíticas.
3. **Given** a coleta em andamento, **When** o processamento avança pelas etapas
   (coleta acadêmica, coleta de mercado, consolidação), **Then** o usuário vê o
   progresso de cada etapa em tempo real, incluindo quantas evidências foram coletadas.
4. **Given** um tema com pouca cobertura pública (ex.: termo muito obscuro), **When** a
   coleta encontra menos evidências que o mínimo confiável, **Then** o painel é entregue
   com aviso explícito de baixa sustentação e as seções sem evidência são marcadas como
   inferência ou omitidas — nunca preenchidas com afirmações sem lastro.

---

### User Story 2 - Consultar histórico e reabrir relatórios (Priority: P2)

O usuário acessa a lista de relatórios já gerados, com tema e data, e reabre qualquer um
deles instantaneamente, sem nova coleta. Isso serve tanto ao uso real (acompanhar temas ao
longo do tempo) quanto à resiliência da demonstração presencial (rede ou fontes externas
podem falhar ao vivo).

**Why this priority**: Segunda maior fonte de valor (histórico consultável) e requisito
de resiliência de demo da constituição (Princípio IV). Depende da US1 existir, por isso P2.

**Independent Test**: Gerar dois relatórios, fechar a sessão, reabrir a plataforma e
verificar que ambos aparecem no histórico e abrem completos sem acesso às fontes externas.

**Acceptance Scenarios**:

1. **Given** relatórios gerados anteriormente, **When** o usuário abre a plataforma,
   **Then** vê o histórico com tema, data de geração e resumo do grau de suporte de cada
   relatório.
2. **Given** o histórico exibido, **When** o usuário seleciona um relatório, **Then** o
   painel completo é exibido em poucos segundos, sem nova coleta.
3. **Given** um tema já pesquisado anteriormente, **When** o usuário solicita o mesmo tema
   novamente, **Then** o sistema oferece a opção de reabrir o relatório existente ou gerar
   uma nova análise atualizada.

---

### User Story 3 - Explorar as evidências em detalhe (Priority: P3)

O usuário aprofunda-se na base de evidências de um relatório: vê a lista completa de
evidências coletadas, filtra por tipo de fonte (científica, consultoria/mercado, notícia,
corporativa, patente), e identifica onde as fontes convergem e divergem entre si.

**Why this priority**: Diferencial de transparência que sustenta a confiança no painel e
rende argumentos na arguição da banca, mas o painel (US1) já entrega grau de suporte
resumido por seção sem esta exploração detalhada.

**Independent Test**: Abrir um relatório gerado e verificar que a visão de evidências
lista todos os itens coletados com tipo, origem e data, filtráveis por tipo de fonte.

**Acceptance Scenarios**:

1. **Given** um relatório aberto, **When** o usuário acessa a visão de evidências,
   **Then** vê todas as evidências com título, tipo de fonte, origem, data e link.
2. **Given** a visão de evidências, **When** o usuário filtra por um tipo de fonte,
   **Then** a lista exibe apenas evidências daquele tipo, com contagem por categoria.
3. **Given** um tema com posições conflitantes entre fontes, **When** o usuário examina a
   seção correspondente, **Then** a divergência é apresentada explicitamente (o que cada
   grupo de fontes sustenta), em vez de uma média artificial.

---

### Edge Cases

- **Tema ambíguo ou muito amplo** (ex.: "IA"): o sistema deve prosseguir com a
  interpretação mais provável, explicitando no painel o recorte adotado.
- **Tema sem evidências suficientes**: painel entregue com aviso de baixa sustentação
  (ver US1, cenário 4); nunca inventar conteúdo.
- **Falha de uma fonte durante a coleta** (indisponibilidade, limite de acesso): o
  pipeline continua com as demais fontes e o painel informa quais categorias de fonte
  ficaram indisponíveis naquela execução.
- **Falha total de coleta** (sem rede): o sistema informa o erro claramente e oferece o
  histórico de relatórios já gerados.
- **Coleta demorada**: o usuário vê progresso por etapa; a execução tem limite máximo de
  tempo e entrega parcial com aviso caso o limite seja atingido.
- **Tema informado em português com fontes majoritariamente em inglês**: a busca deve
  cobrir os dois idiomas e o painel é sempre apresentado em português.
- **Duplicidade de evidências** (mesmo conteúdo em fontes diferentes): evidências
  redundantes são consolidadas, sem inflar artificialmente o grau de suporte.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST aceitar um tema de interesse em texto livre (tendência,
  tecnologia ou conceito) como entrada única para gerar uma análise.
- **FR-002**: O sistema MUST coletar evidências automaticamente em fontes públicas de
  pelo menos duas naturezas distintas: literatura científica estruturada (artigos e
  metadados acadêmicos) e conteúdo de mercado via busca na web (notícias especializadas,
  relatórios públicos de consultorias, publicações corporativas e sinais de patentes).
- **FR-003**: A coleta de mercado MUST formular múltiplas perguntas sob perspectivas
  diferentes do tema (técnica, econômica, industrial, regulatória) para diversificar as
  evidências recuperadas, e MUST registrar a origem de cada evidência.
- **FR-004**: O sistema MUST consolidar as evidências em um painel executivo com as
  seguintes seções: definição do tema, nível de maturidade, principais aplicações,
  setores impactados, empresas e instituições relevantes, investimentos e movimentos de
  mercado, sinais de adoção, oportunidades, desafios e riscos, e perspectivas futuras.
- **FR-005**: Cada seção do painel MUST exibir grau de suporte baseado nas evidências:
  quantidade de fontes, diversidade de tipos de fonte e indicação de convergência ou
  divergência entre elas.
- **FR-006**: Toda afirmação do painel MUST ser rastreável a evidências com referência
  verificável (título, origem, endereço e data quando disponível); afirmações sem
  evidência MUST ser marcadas explicitamente como inferência analítica.
- **FR-007**: O sistema MUST eliminar redundâncias entre evidências equivalentes antes de
  computar o grau de suporte.
- **FR-008**: O sistema MUST apresentar o progresso da análise por etapa (coleta por
  categoria de fonte e consolidação) enquanto a execução ocorre.
- **FR-009**: O sistema MUST persistir cada relatório gerado, com tema, data e conteúdo
  completo, e disponibilizá-lo em um histórico consultável.
- **FR-010**: O sistema MUST permitir reabrir qualquer relatório do histórico sem nova
  coleta e sem dependência de fontes externas no momento da leitura.
- **FR-011**: Quando o usuário solicitar um tema já analisado, o sistema MUST oferecer a
  escolha entre reabrir o relatório existente ou gerar nova análise.
- **FR-012**: A falha de qualquer fonte individual MUST NOT abortar a análise; o sistema
  MUST prosseguir com as fontes disponíveis e informar no painel quais categorias
  ficaram indisponíveis.
- **FR-013**: O sistema MUST impor limite máximo de duração à análise e, ao atingi-lo,
  entregar o resultado parcial com aviso, em vez de falhar silenciosamente.
- **FR-014**: O painel MUST ser apresentado em português brasileiro, ainda que as
  evidências estejam em outros idiomas; referências mantêm o título original.
- **FR-015**: O usuário MUST poder visualizar a lista completa de evidências de um
  relatório, com tipo de fonte, origem, data e link, filtrável por tipo de fonte.

### Key Entities

- **Consulta (Tema)**: pedido de análise feito pelo usuário; atributos: texto do tema,
  data/hora, situação (em andamento, concluída, parcial, falha).
- **Evidência**: unidade de informação coletada; atributos: título, tipo de fonte
  (científica, consultoria/mercado, notícia, corporativa, patente), origem, endereço,
  data de publicação, resumo/trecho relevante, idioma. Relaciona-se a uma Consulta e às
  Seções que sustenta.
- **Relatório (Painel Executivo)**: resultado consolidado de uma Consulta; contém as 10
  seções temáticas, o conjunto de Evidências, os graus de suporte por seção e os avisos
  de degradação/parcialidade. Persistido para o histórico.
- **Seção do Painel**: bloco temático do Relatório (ex.: maturidade, riscos); atributos:
  conteúdo analítico, grau de suporte (contagem e tipos de fontes, convergência),
  referências associadas, marcações de inferência.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Para um tema de tecnologia industrial conhecido, o painel completo é
  entregue em até 5 minutos a partir da solicitação.
- **SC-002**: 100% das seções do painel exibem referências verificáveis com link ativo ou
  marcação explícita de inferência analítica — nenhuma afirmação órfã.
- **SC-003**: Relatórios do histórico abrem em menos de 5 segundos, sem acesso a fontes
  externas.
- **SC-004**: Com uma categoria inteira de fontes indisponível, a análise conclui e o
  painel informa a degradação — taxa de conclusão de 100% nesse cenário.
- **SC-005**: Para temas de tecnologia industrial consolidados (ex.: os dois exemplos do
  desafio), o painel agrega evidências de pelo menos 3 tipos de fonte distintos.
- **SC-006**: Um avaliador consegue, sem instrução prévia, localizar a fonte de qualquer
  afirmação do painel em até 2 cliques (referência na seção → link da evidência).
- **SC-007**: A demonstração completa (novo tema + histórico + exploração de evidências)
  é executável em menos de 10 minutos, compatível com os 20 minutos de apresentação.

## Assumptions

- Usuário único (analista/diretoria) no MVP; sem autenticação, perfis ou controle de
  acesso — múltiplos usuários são evolução futura declarada.
- O painel é sempre gerado em português brasileiro; a coleta cobre ao menos português e
  inglês (predominância de fontes em inglês é esperada e aceitável).
- Fontes pagas (relatórios completos de consultorias como Gartner/McKinsey) são cobertas
  apenas pelo material público disponível (sumários, press releases, cobertura de
  imprensa especializada); acesso a conteúdo assinado está fora de escopo.
- Patentes são cobertas por sinais encontrados via busca pública (bases de patentes
  indexadas na web e notícias de depósitos); integração com base dedicada de patentes é
  evolução futura declarada.
- Retenção de relatórios: indefinida no MVP (volume esperado é baixo — uso individual).
- Agendamento/monitoramento contínuo de temas está fora de escopo do MVP (evolução
  futura declarada).
- A infraestrutura de nuvem e os serviços de IA definidos na constituição do projeto
  (`.specify/memory/constitution.md`) estão disponíveis e provisionáveis dentro do prazo.
- A demonstração presencial poderá ser executada a partir de relatórios já persistidos
  caso a rede do local falhe (Princípio IV da constituição).
