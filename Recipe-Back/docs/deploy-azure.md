# Azure Container Apps デプロイ手順

## 概要

本サービスは Azure Container Apps を用いてホスティングする。
コンテナイメージを Azure Container Registry (ACR) に push し、Container Apps から参照する構成。

GitHub Actions から **手動トリガー** でデプロイ・停止を行い、不要なアクセスを防ぐ。

```
GitHub Actions（手動実行）
    └─→ docker build & push → Azure Container Registry (ACR)
                    └─→ Azure Container Apps（リビジョン更新）
```

停止時はリビジョンを非アクティブ化し、エンドポイントへのアクセスを遮断する。

---

## 費用概算（Azure for Students 対応）

| リソース | SKU | 月額概算 |
|---|---|---|
| Azure Container Registry | Basic | ~$5 |
| Azure Container Apps | リクエスト課金 (min-replicas=0) | ~$0–3 |
| **合計** | | **~$5–8/月** |

Azure for Students の年間クレジット ($100) の範囲内で運用できる。
`min-replicas=0` の設定により、リクエストがない間はインスタンスが停止しコストがほぼ発生しない。

---

## 事前準備

- Azure アカウント（Azure for Students 可）
- Azure CLI のインストール: https://learn.microsoft.com/cli/azure/install-azure-cli
- Docker のインストール

---

## 1. Azure リソースの作成

以下の変数は環境に合わせて変更すること。`ACR_NAME` はグローバルで一意である必要がある。

```bash
RG=recipe-back-rg
LOCATION=japaneast
ACR_NAME=recipebackacr
APP_ENV=recipe-back-env
APP_NAME=recipe-back-app
SP_NAME=recipe-back-sp
```

### 1-1. リソースグループ

```bash
az login
az group create --name $RG --location $LOCATION
```

### 1-2. Azure Container Registry (ACR)

```bash
az acr create --resource-group $RG --name $ACR_NAME --sku Basic
```

### 1-3. Container Apps 環境

```bash
az containerapp env create \
  --name $APP_ENV \
  --resource-group $RG \
  --location $LOCATION
```

### 1-4. Container App（初回作成）

```bash
az containerapp create \
  --name $APP_NAME \
  --resource-group $RG \
  --environment $APP_ENV \
  --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest \
  --target-port 8080 \
  --ingress external \
  --min-replicas 0 --max-replicas 3
```

### 1-5. HTTPS のみ許可

```bash
az containerapp ingress update \
  --name $APP_NAME \
  --resource-group $RG \
  --allow-insecure false
```

---

## 2. サービスプリンシパルの作成（GitHub Actions 用）

GitHub Actions が Azure を操作するためのサービスプリンシパルを作成する。

```bash
# サブスクリプション ID を確認
az account show --query id -o tsv

# サービスプリンシパルを作成（出力 JSON を AZURE_CREDENTIALS に使用）
az ad sp create-for-rbac \
  --name $SP_NAME \
  --role contributor \
  --scopes /subscriptions/<SUBSCRIPTION_ID>/resourceGroups/$RG \
  --sdk-auth
```

出力された JSON はそのまま `AZURE_CREDENTIALS` シークレットに設定する（後述）。

```bash
# サービスプリンシパルに ACR への push 権限を付与
ACR_ID=$(az acr show --name $ACR_NAME --query id -o tsv)
SP_CLIENT_ID=$(az ad sp list --display-name $SP_NAME --query '[0].appId' -o tsv)

az role assignment create \
  --assignee $SP_CLIENT_ID \
  --role AcrPush \
  --scope $ACR_ID
```

---

## 3. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions → New repository secret で以下を登録する。

| シークレット名 | 取得方法 |
|---|---|
| `AZURE_CREDENTIALS` | 手順 2 の `az ad sp create-for-rbac --sdk-auth` の出力 JSON |
| `AZURE_RESOURCE_GROUP` | `recipe-back-rg` |
| `AZURE_REGISTRY_LOGIN_SERVER` | `recipebackacr.azurecr.io` |
| `AZURE_REGISTRY_USERNAME` | `az acr credential show --name $ACR_NAME --query username -o tsv` |
| `AZURE_REGISTRY_PASSWORD` | `az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv` |
| `AZURE_CONTAINER_APP_NAME` | `recipe-back-app` |
| `OPENAI_API_KEY` | OpenAI の API キー |
| `FRIDGE_API_BASE_URL` | Fridge サービスのベース URL |

---

## 4. GitHub Actions ワークフロー

`.github/workflows/` に 2 つのワークフローが用意されている。

| ファイル | 用途 | トリガー |
|---|---|---|
| `deploy.yml` | ビルド・push・デプロイ | 手動 (workflow_dispatch) |
| `stop.yml` | 全リビジョン停止 | 手動 (workflow_dispatch) |

### デプロイ手順

1. GitHub リポジトリ → Actions タブを開く
2. 左サイドバーから "Build and Deploy to Azure Container Apps" を選択
3. "Run workflow" ボタンをクリック → Run workflow を実行
4. `build-and-push` → `deploy` の順にジョブが実行される

### 停止手順

1. GitHub リポジトリ → Actions タブを開く
2. 左サイドバーから "Stop Container App" を選択
3. "Run workflow" ボタンをクリック → Run workflow を実行
4. アクティブなリビジョンがすべて非アクティブ化される

---

## 5. 動作確認

デプロイ後、Container App のエンドポイント URL を確認してヘルスチェックを行う。

```bash
# エンドポイント URL の確認
az containerapp show \
  --name recipe-back-app \
  --resource-group recipe-back-rg \
  --query properties.configuration.ingress.fqdn -o tsv

# ヘルスチェック
curl https://<FQDN>/api/v1/health
# -> 200 OK
```

停止後は 503 が返ることを確認する。

```bash
curl https://<FQDN>/api/v1/health
# -> 503 Service Unavailable
```

---

## ローカルでの動作確認

デプロイ前にローカルでコンテナ動作を確認する場合:

```bash
cd Recipe-Back
docker build -t recipe-back .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=<your_key> \
  -e FRIDGE_API_BASE_URL=<url> \
  recipe-back

curl http://localhost:8080/api/v1/health
```

デバッグモード（OpenAI をスタブに差し替え）で起動する場合:

```bash
docker run -p 8080:8080 -e DEBUG=true recipe-back
```

---

## トラブルシューティング

### ワークフローが失敗する

- `AZURE_CREDENTIALS` の JSON が正しいか確認する（改行・余分なスペースがないこと）
- サービスプリンシパルの有効期限が切れていないか確認する:
  ```bash
  az ad sp show --id <SP_CLIENT_ID> --query appOwnerOrganizationId
  ```

### ACR への push が失敗する

- サービスプリンシパルに `AcrPush` ロールが付与されているか確認する:
  ```bash
  az role assignment list --assignee <SP_CLIENT_ID> --scope <ACR_ID>
  ```

### Container App が起動しない

- コンテナのログを確認する:
  ```bash
  az containerapp logs show \
    --name recipe-back-app \
    --resource-group recipe-back-rg \
    --follow
  ```
- 環境変数 (`OPENAI_API_KEY`, `FRIDGE_API_BASE_URL`) が正しく設定されているか確認する
