# Quickstart: Radar de Tendências Tecnológicas

**Date**: 2026-07-03 | **Feature**: 001-radar-tendencias

## 1. Rodar localmente

```bash
# Pré-requisitos: Python 3.11+, conta Azure com projeto AI Foundry ativo
git clone <repo> && cd research-hub
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configuração (copiar e preencher)
cp .env.example .env
```

`.env` (nunca commitado):

```env
PROJECT_ENDPOINT=https://<foundry-project>.services.ai.azure.com/api/projects/<name>
MODEL_DEPLOYMENT_NAME=gpt-4.1
BING_CONNECTION_ID=/subscriptions/.../connections/<bing-grounding-connection>
COSMOS_ENDPOINT=https://<account>.documents.azure.com:443/
COSMOS_KEY=<primary-key>
ANALYSIS_BUDGET_SECONDS=360
MAX_ANALYSES_PER_DAY=10
# RADAR_OFFLINE=1   # demo offline: repositório em disco (data/reports/) em vez do Cosmos
```

```bash
# Autenticação Azure local (DefaultAzureCredential usa o az login)
az login

# Subir a UI
python -m streamlit run app/Home.py
# → http://localhost:8501
```

## 2. Testes

```bash
pytest                      # unit + integration (tudo mockado, sem custo/credencial)
pytest -m live              # smoke test real (exige .env válido; consome tokens/RU)
```

## 3. Provisionar Azure (uma vez) — detalhes em infra/provision.md

```bash
RG=rg-radar-tendencias
az group create -n $RG -l eastus2

# Cosmos DB serverless + database/container
az cosmosdb create -n cosmos-radar -g $RG --capabilities EnableServerless
az cosmosdb sql database create -a cosmos-radar -g $RG -n radar
az cosmosdb sql container create -a cosmos-radar -g $RG -d radar \
  -n reports --partition-key-path /theme_slug

# Grounding with Bing Search (mesmo RG do projeto Foundry) + conexão no projeto
# (portal: Foundry > Connections > Grounding with Bing Search)

# App Service Linux B1 + deploy (Always On evita cold start na demo)
az webapp up -n app-radar-tendencias -g $RG --runtime PYTHON:3.11 --sku B1
az webapp config set -n app-radar-tendencias -g $RG --always-on true \
  --startup-file "python -m streamlit run app/Home.py --server.port 8000 --server.address 0.0.0.0 --server.headless true"
az webapp config appsettings set -n app-radar-tendencias -g $RG --settings \
  PROJECT_ENDPOINT=... MODEL_DEPLOYMENT_NAME=gpt-4.1 BING_CONNECTION_ID=... \
  COSMOS_ENDPOINT=... COSMOS_KEY=... MAX_ANALYSES_PER_DAY=10 \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true

# OBRIGATÓRIO p/ produção: Managed Identity + role no projeto Foundry
# (DefaultAzureCredential no App Service só autentica via MI — sem isso, 401 no Foundry)
PRINCIPAL_ID=$(az webapp identity assign -n app-radar-tendencias -g $RG --query principalId -o tsv)
az role assignment create --assignee $PRINCIPAL_ID \
  --role "Azure AI User" --scope <resource-id-do-projeto-Foundry>

# Freios de custo (R10): allowlist de IP (liberar na demo) + budget alert
az webapp config access-restriction add -n app-radar-tendencias -g $RG \
  --rule-name allow-apresentador --action Allow --ip-address <seu-ip>/32 --priority 100
az consumption budget create --budget-name radar-budget --amount 30 \
  --time-grain Monthly --category Cost   # ajuste de sintaxe conforme subscription
```

## 4. Fluxo de demo (roteiro de 10 min — SC-007)

1. Abrir app → informar tema novo (ex.: "Robôs Humanoides para Indústria") → mostrar
   progresso por etapa (acadêmica / mercado / consolidação).
2. Painel gerado: percorrer 2-3 seções, destacar badges de grau de suporte e clicar em
   uma referência (2 cliques até a fonte — SC-006).
3. Página Evidências: filtrar por tipo de fonte, mostrar divergência se houver.
4. Histórico: reabrir relatório pré-gerado instantaneamente.

**Planos B em camadas** (Princípio IV): (a) APIs externas falham → painel degradado com
aviso; (b) pipeline falha ao vivo → histórico no Cosmos; (c) rede do local cai →
`RADAR_OFFLINE=1` no notebook do apresentador com relatórios exportados em
`data/reports/` (R9); (d) último recurso → export HTML/PDF estático.

**Antes da apresentação**: exportar 2-3 relatórios do Cosmos para `data/reports/`,
testar o modo offline e liberar o IP do local nas Access Restrictions.
