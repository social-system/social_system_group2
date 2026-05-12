# AWS App Runner デプロイ手順

## 概要

本サービスは AWS App Runner を用いてホスティングする。
コンテナイメージを Amazon ECR に push し、App Runner から参照する構成。

```
GitHub push (main ブランチ)
    └─→ GitHub Actions
            └─→ docker build & push → Amazon ECR
                        └─→ AWS App Runner（自動更新）
```

---

## 事前準備

- AWS アカウント（IAM ユーザーにて操作）
- AWS CLI のインストールと認証設定（`aws configure`）
- Docker のインストール

---

## 1. IAM ユーザーへの権限付与

GitHub Actions から ECR への push に必要な権限を IAM ユーザーに付与する。
必要な権限（インラインポリシーまたはマネージドポリシーで付与）:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*"
    }
  ]
}
```

IAM コンソール → ユーザー → 対象ユーザー → セキュリティ認証情報 → アクセスキーを作成し、後続の手順で使用する。

---

## 2. Amazon ECR リポジトリの作成

```bash
aws ecr create-repository --repository-name recipe-back --region ap-northeast-1
```

出力の `repositoryUri` を控えておく（例: `123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/recipe-back`）。

---

## 3. GitHub Secrets の設定

リポジトリの Settings → Secrets and variables → Actions → New repository secret で以下を登録する。

| Secret 名 | 値 |
|---|---|
| `AWS_ACCESS_KEY_ID` | IAM ユーザーのアクセスキー ID |
| `AWS_SECRET_ACCESS_KEY` | IAM ユーザーのシークレットアクセスキー |

---

## 4. 初回イメージのビルド & プッシュ

GitHub Actions が設定済みであれば `main` ブランチへの push で自動実行される。
手動で行う場合は以下を実行する。

```bash
# ECR にログイン
aws ecr get-login-password --region ap-northeast-1 | \
  docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com

# ビルド & プッシュ（Recipe-Back/ ディレクトリから実行）
cd Recipe-Back
docker build -t recipe-back .
docker tag recipe-back:latest <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/recipe-back:latest
docker push <ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/recipe-back:latest
```

---

## 5. App Runner サービスの作成

AWS コンソール（App Runner）で以下の設定でサービスを作成する。

### ソース設定

| 項目 | 値 |
|---|---|
| ソースの種類 | Amazon ECR |
| コンテナイメージ URI | `<ACCOUNT_ID>.dkr.ecr.ap-northeast-1.amazonaws.com/recipe-back:latest` |
| デプロイトリガー | 自動（ECR push 時に自動更新） |
| ECR アクセスロール | 新規作成（App Runner が ECR を参照するためのロール） |

### サービス設定

| 項目 | 値 |
|---|---|
| ポート | `8080` |
| vCPU | 0.25 vCPU |
| メモリ | 0.5 GB |

### 環境変数

| 変数名 | 値 |
|---|---|
| `OPENAI_API_KEY` | OpenAI の API キー |
| `FRIDGE_API_BASE_URL` | Fridge サービスのベース URL |
| `PORT` | `8080` |

> `OPENAI_API_KEY` は機密情報のため、AWS Secrets Manager に登録して参照することを推奨する。

---

## 6. 動作確認

App Runner のコンソールからサービス URL（`https://xxxxxx.ap-northeast-1.awsapprunner.com`）を確認し、以下でヘルスチェックを行う。

```bash
curl https://<APP_RUNNER_URL>/api/v1/health
# -> 200 OK
```

---

## ローカルでの動作確認

デプロイ前にローカルでコンテナ動作を確認する場合:

```bash
cd Recipe-Back
docker build -t recipe-back .
docker run -p 8080:8080 -e OPENAI_API_KEY=<your_key> -e FRIDGE_API_BASE_URL=<url> recipe-back
curl http://localhost:8080/api/v1/health
```

デバッグモード（OpenAI をスタブに差し替え）で起動する場合:

```bash
docker run -p 8080:8080 -e DEBUG=true recipe-back
```

---

## 費用概算

最小構成（0.25 vCPU / 0.5 GB）での概算:

| 期間 | 費用 |
|---|---|
| 1日（低トラフィック） | 約 $0.15〜$0.50 |
| 1ヶ月 | 約 $6〜$11 |
