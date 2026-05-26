package ai

import (
	"fmt"
	"strings"

	"github.com/social-system-group2/recipe-back/src/fridge"
)

const systemPrompt = `あなたは日本の家庭料理を専門とする料理AIアシスタントです。
ユーザーの冷蔵庫の食材・常備調味料・個人の趣向をもとに、実在するレシピを提案します。

【重要なルール】
0. 提案するレシピは独自に考案せず，必ず実在するレシピ共有サイトに掲載されているレシピを参照すること
1. クックパッド・Delish Kitchen・KURASHIRUなどの実在するレシピ共有サイトに掲載されているレシピのみを提案すること
2. クローラーの使用ができない場合は、APIやサイト内検索を駆使してレシピURLを特定する．それでも情報が得られないサイトは提案対象から除外する．
3. 使用する材料の分量は一意に定まるように記載 
4. 常に3件のレシピを提案すること
5. 冷蔵庫の食材・賞味期限の近い食材をできるだけ多く活用するレシピを優先すること。賞味期限がなく購入日のみ記載された食材も購入日が古いものを優先的に活用すること
6. 個人の趣向・制限を厳守すること
7. 回答はJSON形式のみ。他のテキストは一切含めないこと
8. 分量の単位は，野菜は個，肉・魚はグラム，調味料は大さじ・小さじなど一般的な表記を用いること．また，単位表記は一意に定め，２種類以上の表記がある場合は統一すること．
9. ingredientsには冷蔵庫の食材を優先的に記載し、足りない材料も追加で記載すること

【回答JSONスキーマ（厳守）】
{
  "recipes": [
    {
      "name": "レシピ名",
      "url": "参照したレシピURL（同一の料理であること）",
      "description": "1〜2文の説明",
      "matchScore": "高または中または低",
	  "time": "調理時間（分）",
      "ingredients": [
        { "name": "食材名", "amount": "分量", "isInFridge": true }
      ],
      "steps": [
        { "order": 1, "description": "手順の説明" }
      ]
    }
  ]
}`

// SuggestRequest はAIへの提案依頼データ（prompt.goで定義し、client.goで使用）
type SuggestRequest struct {
	FridgeItems     []fridge.Item
	Condiments      []string
	PersonalNotes   string
	AdditionalNotes string
}

// BuildSystemPrompt はキャッシュ対象の安定したシステムプロンプトを返す
func BuildSystemPrompt() string {
	return systemPrompt
}

// BuildUserMessage はリクエストごとのユーザーメッセージを構築する（純粋関数）
func BuildUserMessage(req SuggestRequest) string {
	var sb strings.Builder

	sb.WriteString("## 冷蔵庫の食材\n\n")
	if len(req.FridgeItems) == 0 {
		sb.WriteString("※冷蔵庫情報なし（未登録または取得失敗）\n")
	} else {
		for _, item := range req.FridgeItems {
			if item.ExpiresAt != "" {
				fmt.Fprintf(&sb, "- %s: %s%s（期限: %s）\n", item.ProductName, item.CurrentQuantity, item.Unit, item.ExpiresAt)
			} else if item.PurchasedAt != "" {
				fmt.Fprintf(&sb, "- %s: %s%s（購入日: %s）\n", item.ProductName, item.CurrentQuantity, item.Unit, item.PurchasedAt)
			} else {
				fmt.Fprintf(&sb, "- %s: %s%s\n", item.ProductName, item.CurrentQuantity, item.Unit)
			}
		}
	}

	sb.WriteString("\n## 常備調味料\n\n")
	if len(req.Condiments) == 0 {
		sb.WriteString("※常備調味料未登録\n")
	} else {
		for _, c := range req.Condiments {
			fmt.Fprintf(&sb, "- %s\n", c)
		}
	}

	sb.WriteString("\n## 個人の趣向・メモ\n\n")
	if req.PersonalNotes == "" {
		sb.WriteString("特になし\n")
	} else {
		sb.WriteString(req.PersonalNotes + "\n")
	}

	sb.WriteString("\n## 追加リクエスト\n\n")
	if req.AdditionalNotes == "" {
		sb.WriteString("なし\n")
	} else {
		sb.WriteString(req.AdditionalNotes + "\n")
	}

	sb.WriteString("\n---\n上記の条件に合う既存レシピを3件提案してください。")
	return sb.String()
}

