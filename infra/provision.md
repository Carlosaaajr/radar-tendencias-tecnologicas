# Provisionamento Azure — Radar de Tendências Tecnológicas

**Data**: 2026-07-04 | **Resource Group**: `radar-trends` (reaproveitado — existia vazio
na assinatura) | **Assinatura**: Azure subscription 1

**Região final: `brazilsouth`** (não eastus/eastus2 do plano original) — a região
`eastus` estava genuinamente sem capacidade para novas contas Cosmos DB no momento do
deploy (`ServiceUnavailable` real da Azure, confirmado 2x mesmo sem zone redundancy).
Migrado para `brazilsouth`, a mesma região do projeto Foundry (`omc-cli/omc-ccg-cli`) —
elimina também a latência cross-region entre App Service e agentes. Ver
`docs/critical-review.md` para o relato completo do atrito de provisionamento.

## 1. Cosmos DB serverless

```bash
RG=radar-trends
COSMOS_ACCOUNT=cosmos-radar-tendencias

# Location omitida -> usa a do resource group; zone redundancy explicitamente desligada
# (necessário — algumas regiões rejeitam contas zonais por falta de capacidade)
az cosmosdb create -n $COSMOS_ACCOUNT -g $RG --capabilities EnableServerless \
  --locations regionName=brazilsouth failoverPriority=0 isZoneRedundant=False

az cosmosdb sql database create -a $COSMOS_ACCOUNT -g $RG -n radar

# MSYS_NO_PATHCONV=1 necessário no Git Bash (Windows) — sem isso, "/theme_slug" é
# expandido como caminho de arquivo local pelo bash
MSYS_NO_PATHCONV=1 az cosmosdb sql container create -a $COSMOS_ACCOUNT -g $RG -d radar \
  -n reports --partition-key-path /theme_slug
```

## 2. App Service Linux B1

```bash
LOCATION=brazilsouth
APP_NAME=radar-tendencias-app
PLAN_NAME=radar-tendencias-plan

az appservice plan create -n $PLAN_NAME -g $RG -l $LOCATION --is-linux --sku B1
az webapp create -n $APP_NAME -g $RG -p $PLAN_NAME --runtime "PYTHON:3.11"
az webapp config set -n $APP_NAME -g $RG --always-on true \
  --startup-file "python -m streamlit run app/Home.py --server.port 8000 --server.address 0.0.0.0 --server.headless true"

# OBRIGATÓRIO — az webapp create cria o app com webSocketsEnabled=false por padrão;
# Streamlit depende de WebSocket para atualizar a UI (achado real do deploy)
az webapp config set -n $APP_NAME -g $RG --web-sockets-enabled true
```

## 3. Managed Identity + role no projeto Foundry (obrigatório — R1)

```bash
PRINCIPAL_ID=$(az webapp identity assign -n $APP_NAME -g $RG --query principalId -o tsv)
```

**⚠️ PENDENTE — ação manual necessária.** A role original do plano ("Azure AI User") não
existe mais nesta assinatura; a Azure reorganizou as roles do Foundry. `az role
assignment create` falha de forma reproduzível com `MissingSubscription` para as roles
novas (`Foundry User`, `Foundry Project Runtime User`, `Foundry Agent Consumer`) tanto
por nome quanto por GUID, em qualquer escopo testado (conta e projeto) — não é
flakiness de rede, é uma limitação real do CLI/API nesta combinação de recursos no
momento do deploy.

**Atribuir manualmente no portal**: `portal.azure.com` → recurso `omc-cli`
(`ai-models-resource`) → **Access control (IAM)** → **Add role assignment** → role
**"Foundry User"** → Assign access to **Managed Identity** → selecionar `radar-tendencias-app`.

O código já usa `DefaultAzureCredential` — funciona automaticamente assim que a role
existir, sem qualquer mudança de código.

## 4. App Settings

```bash
az webapp config appsettings set -n $APP_NAME -g $RG --settings \
  PROJECT_ENDPOINT="https://omc-cli.services.ai.azure.com/api/projects/omc-ccg-cli" \
  MODEL_DEPLOYMENT_NAME="gpt-5-radar" \
  COSMOS_ENDPOINT="https://$COSMOS_ACCOUNT.documents.azure.com:443/" \
  COSMOS_KEY="$(az cosmosdb keys list -n $COSMOS_ACCOUNT -g $RG --query primaryMasterKey -o tsv)" \
  MAX_ANALYSES_PER_DAY="10" \
  ANALYSIS_BUDGET_SECONDS="360" \
  SCM_DO_BUILD_DURING_DEPLOYMENT="true"
```

## 5. Deploy (zip deploy)

```bash
cd research-hub
zip -r ../deploy.zip . -x ".venv/*" -x ".git/*" -x "data/reports/*.json" \
  -x "__pycache__/*" -x "*/__pycache__/*" -x ".pytest_cache/*" -x ".ruff_cache/*" \
  -x ".env" -x "tests/fixtures/_tmp_*/*"
az webapp deploy -n $APP_NAME -g $RG --src-path ../deploy.zip --type zip
```

## 6. Freios de custo (R10)

```bash
# Access Restriction — liberar apenas o IP do apresentador (fazer na hora da demo — T040,
# não antes, pois o IP muda conforme o local da apresentação)
az webapp config access-restriction add -n $APP_NAME -g $RG \
  --rule-name allow-apresentador --action Allow --ip-address <SEU_IP>/32 --priority 100
```

**⚠️ PENDENTE — ação manual necessária.** `az consumption budget create` retorna
`400 Invalid budget configuration, please use filter interface with 2019-05-01-preview
version` de forma reproduzível nesta assinatura, tanto em escopo de subscription quanto
de resource group, com ou sem `--resource-group-filter` (comando em preview, conhecido
por instabilidade). **Criar manualmente no portal**: `portal.azure.com` → **Cost
Management** → **Budgets** → **Add** → escopo `radar-trends` → valor mensal US$30 →
alerta em 80%/100%.

## Notas operacionais do deploy real (2026-07-04)

- **Conexões HTTPS longas instáveis** neste ambiente: `az cosmosdb create`, `az webapp
  create` e `az webapp deploy` sofreram `ConnectionResetError` no meio da chamada
  algumas vezes. Mitigação: rodar em background e verificar o estado via `az ... show`
  (chamadas curtas, que não sofreram o mesmo problema).
- Region `eastus` sem capacidade para Cosmos DB no momento — ver nota no topo.

## Verificação pós-deploy

```bash
curl -s https://$APP_NAME.azurewebsites.net/_stcore/health
```

Smoke test funcional (gerar 1 relatório real) documentado em T036 / `docs/critical-review.md`.
