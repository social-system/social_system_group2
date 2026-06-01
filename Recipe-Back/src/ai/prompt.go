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
3. 分量の単位は，野菜は個，肉・魚はグラム，調味料は大さじ・小さじなど一般的な表記を用いること．また，単位表記は一意に定め，在庫の単位に従うこと．
4. 常に3件のレシピを提案すること
5. 冷蔵庫の食材・賞味期限の近い食材をできるだけ多く活用するレシピを優先すること。賞味期限がなく購入日のみ記載された食材も購入日が古いものを優先的に活用すること
6. 個人の趣向・制限を厳守すること
7. 回答はJSON形式のみ。他のテキストは一切含めないこと
8. ingredientsには冷蔵庫の食材を優先的に記載し、足りない材料も追加で記載すること．また，在庫がある食材の名前は在庫における食材名を採用すること．

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
}
  
【分量の記載方法（厳守）】
以下の例に従って，適切に分量を標準化すること
（期待する記載）
- 200gの鶏肉 → "amount": "200g"
- 1個の玉ねぎ → "amount": "1個"
- 鶏肉200g〜300g → "amount": "200g"
- 小さじ1の塩 → "amount": "小さじ1"
- 玉ねぎ1/2個 → "amount": "0.5個"
- 塩少々 → "amount": "少々"
`

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

const normalizeAmountSystemPrompt = `あなたは料理の分量表記を正規化するAIです。
複数の食材・分量・在庫単位をJSON配列で受け取り、正規化した分量のみをJSON文字列配列で返してください。

【ルール】
- 食材名などの余分な情報は除去する（例: "200gの鶏肉" → "200g"）
- 範囲表記は最小値を採用する（例: "200g〜300g" → "200g"）
- unitフィールドが指定されている場合はその単位に合わせて正規化すること（例: unit="g" なら "鶏肉200g〜300g" → "200g"）
- 複数の単位での表記がされている場合は，unitフィールドの単位を優先すること（例: "200g分（1/6個相当）" で unit="g" なら "200g"）
- 大さじ・小さじなど日本の計量単位はそのまま保持する（例: "小さじ1の塩" → "小さじ1"）
- 分数は小数に変換する（例: "1/2個" → "0.5個"）
- "少々" "適量" などの定性的な表現はそのまま保持する
- 入力と同じ順序・同じ件数でJSON配列を出力すること
- JSON配列のみを出力し、余分なテキストは一切含めないこと`

// buildNormalizeAmountSystemPrompt は分量正規化用のシステムプロンプトを返す
func buildNormalizeAmountSystemPrompt() string {
	return normalizeAmountSystemPrompt
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
