# PROJECT STATUS.md 追記案

以下を既存の `PROJECT STATUS.md` の末尾に追記する。

```md
## 現時点の設計方針

このアプリは、当面は一人用のローカル家計簿として開発する。

そのため、現段階では認証、ユーザー管理、世帯管理、ユーザーごとのデータ分離は実装しない。DB は SQLite を前提とし、ローカル環境での利用を優先する。

次の開発では、レシート登録機能を土台として、登録済みデータを確認・削除できる機能を追加する。具体的には、レシート一覧取得、レシート詳細取得、レシート削除、バリデーション強化、テスト追加を優先する。

更新 API、集計 API、OCR 連携、商品名の正規化、認証機能は、基本的な登録・取得・削除が安定してから検討する。

## 次の開発単位

次の開発は、`doc/milestone/` 配下のマイルストーン文書に従って、1つずつ実装する。

| 順番 | ファイル | 目的 |
| ---: | --- | --- |
| 1 | `doc/milestone/MILESTONE01.md` | リクエストスキーマのバリデーションを強化する |
| 2 | `doc/milestone/MILESTONE02.md` | レシート詳細取得の CRUD 処理を追加する |
| 3 | `doc/milestone/MILESTONE03.md` | `GET /receipts/{receipt_id}` を追加する |
| 4 | `doc/milestone/MILESTONE04.md` | レシート一覧取得の CRUD 処理を追加する |
| 5 | `doc/milestone/MILESTONE05.md` | `GET /receipts` を追加する |
| 6 | `doc/milestone/MILESTONE06.md` | レシート削除の CRUD 処理を追加する |
| 7 | `doc/milestone/MILESTONE07.md` | `DELETE /receipts/{receipt_id}` を追加する |
| 8 | `doc/milestone/MILESTONE08.md` | テスト用 DB 設定を追加する |
| 9 | `doc/milestone/MILESTONE09.md` | 登録、取得、削除、異常系のテストを追加する |

## Codex による実装方針

Codex に実装を依頼する場合は、リポジトリ直下の `AGENTS.md` に従う。

Codex は一度に複数のマイルストーンを進めず、指定された `MILESTONE0X.md` の範囲だけを実装する。マイルストーンの範囲外となる認証、ユーザー管理、OCR、集計 API、DB マイグレーション、広範囲なリファクタリングは行わない。
```
