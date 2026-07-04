<!--
Sync Impact Report
- Version change: (template) → 1.0.0
- Modified principles: n/a (adoção inicial)
- Added sections:
  - Core Principles (I–VI)
  - Restrições Técnicas (stack fixa Azure/Python)
  - Fluxo de Desenvolvimento e Gates de Qualidade
  - Governance
- Removed sections: nenhum
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (gate "Constitution Check" genérico — compatível, preenchido por plano)
  - ✅ .specify/templates/spec-template.md (sem seções obrigatórias adicionais — compatível)
  - ✅ .specify/templates/tasks-template.md (categorias de tarefas cobrem testes/documentação — compatível)
- Follow-up TODOs:
  - .specify/extensions/git/scripts/powershell/initialize-repo.ps1 falha no PowerShell 5.1
    por encoding (✓ UTF-8 sem BOM). Não afeta a constituição; corrigir quando conveniente.
-->

# Radar de Tendências Tecnológicas — Constitution

Plataforma que recebe um tema tecnológico (tendência, tecnologia ou conceito) e gera um
painel executivo fundamentado em evidências verificáveis coletadas na internet, conforme o
desafio "SENAI do Futuro — IA". Projeto: `research-hub`.

## Core Principles

### I. Evidência Rastreável (NON-NEGOTIABLE)

Toda afirmação apresentada no painel executivo MUST ser rastreável a pelo menos uma evidência
coletada, com fonte citada (título, origem, URL e data quando disponível) e grau de suporte
explícito (quantidade e diversidade de fontes que sustentam a afirmação). Conclusões sem
evidência associada MUST ser marcadas como inferência do modelo ou removidas.

Racional: o desafio exige que o usuário compreenda "não apenas o que está sendo afirmado, mas
também o grau de suporte encontrado nas fontes analisadas". Este é o diferencial competitivo
da solução e critério direto de avaliação da banca.

### II. Simplicidade Orientada a Prazo

O MVP MUST ser entregável em 1 semana. Abstrações especulativas, generalizações prematuras e
dependências não essenciais são proibidas. Cada componente novo MUST justificar-se por um
requisito do desafio ou por um critério de avaliação da banca. Na dúvida entre duas soluções,
escolher a mais simples que preserve os Princípios I e IV.

Racional: o prazo é a restrição dominante; complexidade não demonstrável na apresentação de
20 minutos é custo sem retorno.

### III. Azure-First

A plataforma MUST operar na nuvem Azure: aplicação Streamlit no Azure App Service, persistência
no Cosmos DB serverless e agentes de IA implementados no Azure AI Foundry Agent Service
(Agente Coletor com Grounding with Bing Search; Agente Sintetizador). Serviços fora do Azure
são permitidos apenas para fontes de dados públicas (arXiv, OpenAlex/Semantic Scholar).
Credenciais e chaves MUST ser configuradas via variáveis de ambiente ou Azure Key Vault —
nunca hardcoded.

Racional: requisito explícito do usuário e do contexto do desafio; coerência de arquitetura
conta ponto na avaliação de "Arquitetura da solução".

### IV. Resiliência de Demo

Todo relatório gerado MUST ser persistido (cache) no Cosmos DB e recuperável sem nova coleta.
Toda integração com API externa MUST ter tratamento de falha com fallback definido (degradar
para fontes disponíveis, nunca abortar o pipeline inteiro por falha de uma fonte). A demo para
a banca MUST poder ser executada a partir de relatórios cacheados se a rede ou as APIs falharem
ao vivo.

Racional: a apresentação é presencial, com tempo fixo de 20 minutos; falha ao vivo de uma
dependência externa não pode comprometer a avaliação.

### V. Qualidade Avaliável

O código MUST estar organizado em módulos com responsabilidade clara (UI, orquestração, coleta,
síntese, persistência). Os módulos críticos do pipeline (coleta, consolidação, graduação de
evidências) MUST ter testes automatizados. O repositório MUST conter documentação de
arquitetura (diagrama e decisões técnicas com justificativa) e um README com instruções de
execução reproduzíveis.

Racional: "Qualidade de implementação" (organização, boas práticas, documentação, testes,
robustez) é critério explícito da banca.

### VI. Avaliação Crítica Documentada

O projeto MUST manter documentadas: limitações conhecidas da solução, custos estimados de
operação (por consulta e mensal), vieses potenciais (de fontes, de idioma, do modelo de IA) e
evoluções futuras priorizadas. Este documento MUST ser atualizado a cada fase (plan, tasks,
implement) e servirá de base para a seção de avaliação crítica da apresentação.

Racional: "Avaliação crítica" é critério explícito da banca; produzi-la incrementalmente
custa menos que reconstruí-la na véspera.

## Restrições Técnicas

- Linguagem: Python (única linguagem do projeto; full Python com Streamlit).
- UI: Streamlit servido no Azure App Service.
- Agentes: Azure AI Foundry Agent Service — Agente Coletor (Grounding with Bing Search,
  incluindo sinais de patentes via busca direcionada) e Agente Sintetizador (consolidação
  em painel estruturado). Técnica de perguntas multi-perspectiva (inspirada no STORM de
  Stanford) aplicada nos prompts do Coletor.
- Fontes acadêmicas determinísticas: arXiv API e OpenAlex/Semantic Scholar (APIs gratuitas,
  sem chave ou com chave gratuita).
- Patentes: cobertas exclusivamente via Bing grounding (Google Patents e notícias); API
  dedicada (EPO OPS) registrada como evolução futura.
- Persistência: Azure Cosmos DB serverless (relatórios como documentos JSON).
- Dependências pinadas em `requirements.txt`.

## Fluxo de Desenvolvimento e Gates de Qualidade

- Fases seguem o spec-kit: constitution → specify → clarify → plan → tasks → implement,
  com os hooks git da extensão instalada (commits automáticos entre fases quando aceitos).
- O plano de arquitetura MUST passar por revisão do agente octo-cloud-architect antes de
  gerar tasks; blocos significativos de implementação MUST passar por octo-code-reviewer.
- Gate de Constitution Check no plano: cada decisão de design MUST citar qual princípio a
  sustenta; violações exigem justificativa na tabela de Complexity Tracking.
- Commits somente mediante aprovação do usuário ou hooks aceitos; nunca push forçado.

## Governance

Esta constituição prevalece sobre quaisquer outras práticas do repositório. Emendas exigem:
(1) proposta registrada no PR ou na conversa com o usuário, (2) aprovação explícita do usuário,
(3) atualização do Sync Impact Report e incremento de versão semântica — MAJOR para remoção ou
redefinição incompatível de princípio, MINOR para princípio novo ou orientação materialmente
expandida, PATCH para clarificações. Toda revisão de plano, tasks e código MUST verificar
conformidade com os princípios I–VI; não-conformidades MUST ser justificadas na Complexity
Tracking do plano ou corrigidas.

**Version**: 1.0.0 | **Ratified**: 2026-07-03 | **Last Amended**: 2026-07-03
