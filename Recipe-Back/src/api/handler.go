package api

import (
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/social-system-group2/recipe-back/src/ai"
	"github.com/social-system-group2/recipe-back/src/fridge"
	"github.com/social-system-group2/recipe-back/src/user"
)

// RecipeHandler は POST /api/v1/recipes/suggest を処理する
// @Tags recipes
type RecipeHandler struct {
	aiClient     ai.Client
	fridgeClient fridge.Client
	userStore    user.Store
}

// NewRecipeHandler はRecipeHandlerを返す
func NewRecipeHandler(aiClient ai.Client, fridgeClient fridge.Client, userStore user.Store) *RecipeHandler {
	return &RecipeHandler{
		aiClient:     aiClient,
		fridgeClient: fridgeClient,
		userStore:    userStore,
	}
}

// SuggestRecipes はレシピ提案を返す
// @Summary レシピ提案
// @Description 冷蔵庫の食材・常備調味料・個人の趣向をもとにAIがレシピを3件提案する
// @Accept json
// @Produce json
// @Param request body SuggestRecipesRequest false "追加リクエスト（任意）"
// @Success 200 {object} SuggestRecipesResponse
// @Failure 400 {object} ErrorResponse
// @Failure 422 {object} ErrorResponse
// @Failure 502 {object} ErrorResponse
// @Router /api/v1/recipes/suggest [post]
func (h *RecipeHandler) SuggestRecipes(w http.ResponseWriter, r *http.Request) {
	var req SuggestRecipesRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil && err.Error() != "EOF" {
		writeError(w, http.StatusBadRequest, "BAD_REQUEST", "Request body is invalid JSON", "")
		return
	}

	if utf8.RuneCountInString(req.AdditionalNotes) > 1000 {
		writeError(w, http.StatusUnprocessableEntity, "VALIDATION_ERROR",
			"Validation failed", "additionalNotes exceeds maximum length of 1000 characters")
		return
	}

	inventory, err := h.fridgeClient.GetInventory(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR",
			"Failed to get fridge inventory", err.Error())
		return
	}

	prefs, err := h.userStore.GetPreferences(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR",
			"Failed to get user preferences", err.Error())
		return
	}

	aiRecipes, err := h.aiClient.SuggestRecipes(r.Context(), ai.SuggestRequest{
		FridgeItems:     inventory.Items,
		Condiments:      prefs.Condiments,
		PersonalNotes:   prefs.PersonalNotes,
		AdditionalNotes: req.AdditionalNotes,
	})
	if err != nil {
		writeError(w, http.StatusBadGateway, "AI_ERROR",
			"Failed to get recipe suggestions from AI", err.Error())
		return
	}

	writeJSON(w, http.StatusOK, SuggestRecipesResponse{Recipes: convertRecipes(aiRecipes, inventory)})
}

// PreferencesHandler は GET/PUT /api/v1/preferences を処理する
// @Tags preferences
type PreferencesHandler struct {
	userStore user.Store
}

// NewPreferencesHandler はPreferencesHandlerを返す
func NewPreferencesHandler(userStore user.Store) *PreferencesHandler {
	return &PreferencesHandler{userStore: userStore}
}

// GetPreferences はユーザー設定を返す
// @Summary ユーザー設定取得
// @Description 常備調味料と個人の趣向を取得する
// @Produce json
// @Success 200 {object} Preferences
// @Failure 500 {object} ErrorResponse
// @Router /api/v1/preferences [get]
func (h *PreferencesHandler) GetPreferences(w http.ResponseWriter, r *http.Request) {
	prefs, err := h.userStore.GetPreferences(r.Context())
	if err != nil {
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR",
			"Failed to get preferences", err.Error())
		return
	}
	writeJSON(w, http.StatusOK, Preferences{
		Condiments:    prefs.Condiments,
		PersonalNotes: prefs.PersonalNotes,
	})
}

// UpdatePreferences はユーザー設定を更新する
// @Summary ユーザー設定更新
// @Description 常備調味料と個人の趣向を更新する
// @Accept json
// @Produce json
// @Param request body Preferences true "ユーザー設定"
// @Success 200 {object} Preferences
// @Failure 400 {object} ErrorResponse
// @Failure 422 {object} ErrorResponse
// @Failure 500 {object} ErrorResponse
// @Router /api/v1/preferences [put]
func (h *PreferencesHandler) UpdatePreferences(w http.ResponseWriter, r *http.Request) {
	var req Preferences
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "BAD_REQUEST", "Request body is invalid JSON", "")
		return
	}

	if len(req.Condiments) > 50 {
		writeError(w, http.StatusUnprocessableEntity, "VALIDATION_ERROR",
			"Validation failed", "condiments: max 50 items allowed")
		return
	}
	for _, c := range req.Condiments {
		if utf8.RuneCountInString(c) > 50 {
			writeError(w, http.StatusUnprocessableEntity, "VALIDATION_ERROR",
				"Validation failed", "condiments: each item must be 50 characters or less")
			return
		}
	}
	if utf8.RuneCountInString(req.PersonalNotes) > 2000 {
		writeError(w, http.StatusUnprocessableEntity, "VALIDATION_ERROR",
			"Validation failed", "personalNotes exceeds maximum length of 2000 characters")
		return
	}

	if req.Condiments == nil {
		req.Condiments = []string{}
	}

	updated := user.Preferences{
		Condiments:    req.Condiments,
		PersonalNotes: req.PersonalNotes,
	}
	if err := h.userStore.UpdatePreferences(r.Context(), updated); err != nil {
		writeError(w, http.StatusInternalServerError, "INTERNAL_ERROR",
			"Failed to update preferences", err.Error())
		return
	}

	writeJSON(w, http.StatusOK, req)
}

// HealthHandler はヘルスチェックを返す
func HealthHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]string{"status": "ok"})
}

// AcceptRecipe はレシピ受け入れ時に冷蔵庫の在庫を消費する
// @Summary レシピ受け入れ
// @Description 受け入れたレシピの冷蔵庫食材を POST /inventory/movements で消費記録する
// @Accept json
// @Produce json
// @Param request body AcceptRecipeRequest true "受け入れるレシピ情報"
// @Success 200 {object} AcceptRecipeResponse
// @Failure 400 {object} ErrorResponse
// @Failure 422 {object} ErrorResponse
// @Router /api/v1/recipes/accept [post]
func (h *RecipeHandler) AcceptRecipe(w http.ResponseWriter, r *http.Request) {
	var req AcceptRecipeRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeError(w, http.StatusBadRequest, "BAD_REQUEST", "Request body is invalid JSON", "")
		return
	}
	if len(req.Ingredients) == 0 {
		writeError(w, http.StatusUnprocessableEntity, "VALIDATION_ERROR", "Validation failed", "ingredients must not be empty")
		return
	}

	// 冷蔵庫食材のみ抽出してまとめて正規化
	var fridgeIngredients []Ingredient
	for _, ing := range req.Ingredients {
		if ing.IsInFridge && ing.ProductID != 0 {
			fridgeIngredients = append(fridgeIngredients, ing)
		}
	}

	normalizedAmounts := make([]string, len(fridgeIngredients))
	for i, ing := range fridgeIngredients {
		normalizedAmounts[i] = ing.Amount
	}
	if len(fridgeIngredients) > 0 {
		items := make([]ai.NormalizeItem, len(fridgeIngredients))
		for i, ing := range fridgeIngredients {
			items[i] = ai.NormalizeItem{Name: ing.Name, Amount: ing.Amount, Unit: ing.Unit}
		}
		if result, err := h.aiClient.NormalizeAmounts(r.Context(), items); err != nil {
			slog.Warn("amount normalization failed, using originals", "error", err)
		} else {
			normalizedAmounts = result
		}
	}

	var movementsCreated int
	var skipped []string

	stockQty := make(map[int]float64)
	stockUnit := make(map[int]string)
	if inv, err := h.fridgeClient.GetInventory(r.Context()); err == nil {
		for _, item := range inv.Items {
			if v, err := strconv.ParseFloat(item.CurrentQuantity, 64); err == nil {
				stockQty[item.ProductID] += v
				if stockUnit[item.ProductID] == "" {
					stockUnit[item.ProductID] = item.Unit
				}
			}
		}
	}

	now := time.Now()
	for i, ing := range fridgeIngredients {
		quantity, parsedUnit := parseAmount(normalizedAmounts[i])
		unit := ing.Unit
		if unit == "" {
			unit = parsedUnit
		}

		if sQty, ok := stockQty[ing.ProductID]; ok {
			sUnit := stockUnit[ing.ProductID]
			if sUnit != "" && unit != "" && sUnit != unit {
				slog.Warn("unit mismatch, skipping cap", "product_id", ing.ProductID, "recipe_unit", unit, "stock_unit", sUnit)
			} else if recipeQty, err := strconv.ParseFloat(quantity, 64); err == nil {
				if recipeQty > sQty {
					slog.Info("capping quantity to stock", "product_id", ing.ProductID, "recipe_qty", recipeQty, "stock_qty", sQty)
					quantity = strconv.FormatFloat(sQty, 'f', -1, 64)
				}
			}
		}

		movReq := fridge.MovementRequest{
			ProductID:      ing.ProductID,
			MovementType:   "consume",
			Quantity:       quantity,
			Unit:           unit,
			Reason:         fmt.Sprintf("%sで使用", req.RecipeName),
			OccurredAt:     now.Format("2006-01-02T15:04:05"),
		}

		if err := h.fridgeClient.PostMovement(r.Context(), movReq); err != nil {
			slog.Warn("inventory movement failed", "product_id", ing.ProductID, "name", ing.Name, "unit", ing.Unit, "amount", quantity, "error", err)
			skipped = append(skipped, ing.Name)
			continue
		}
		movementsCreated++
	}

	writeJSON(w, http.StatusOK, AcceptRecipeResponse{
		MovementsCreated: movementsCreated,
		Skipped:          skipped,
	})
}

var numericRe = regexp.MustCompile(`^(\d+(?:\.\d+)?)(?:/(\d+))?`)

// parseAmount は "200g", "2個", "大さじ2", "0.5個", "適量" などを (quantity, unit) に変換する。
// 例: "200g" → ("200", "g"), "0.5個" → ("0.5", "個"), "適量" → ("適量", "")
func parseAmount(amount string) (quantity string, unit string) {
	amount = strings.TrimSpace(amount)
	if amount == "" {
		return "", ""
	}

	// 先頭の非数値プレフィックスを抽出（例: "大さじ" in "大さじ2"）
	prefixEnd := 0
	for i, r := range amount {
		if r >= '0' && r <= '9' {
			break
		}
		prefixEnd = i + utf8.RuneLen(r)
	}
	prefix := amount[:prefixEnd]
	rest := amount[prefixEnd:]

	// rest が空 = 数値なし ("適量" など)
	if rest == "" {
		return amount, ""
	}

	m := numericRe.FindStringSubmatch(rest)
	if m == nil {
		// 数値が見つからない場合はそのまま返す
		return amount, ""
	}

	var q float64
	numerator, _ := strconv.ParseFloat(m[1], 64)
	if m[2] != "" {
		// 分数 (例: "1/2")
		denominator, _ := strconv.ParseFloat(m[2], 64)
		if denominator != 0 {
			q = numerator / denominator
		}
	} else {
		q = numerator
	}

	// 数値部分の末尾インデックスを求めてユニット部分を取り出す
	suffix := rest[len(m[0]):]
	unitPart := strings.TrimSpace(prefix + suffix)

	// 数量文字列: 整数なら小数点なし、小数なら必要な桁だけ
	if q == float64(int64(q)) {
		quantity = strconv.FormatInt(int64(q), 10)
	} else {
		quantity = strconv.FormatFloat(q, 'f', -1, 64)
	}
	return quantity, unitPart
}

// normalizeName は商品名・材料名の表記ゆれ（カタカナ⇄ひらがな、余分な空白等）を平滑化する
func normalizeName(s string) string {
	s = strings.TrimSpace(s)
	s = strings.ReplaceAll(s, "　", "")
	return katakanaToHiragana(s)
}

func katakanaToHiragana(s string) string {
	var b strings.Builder
	for _, r := range s {
		// カタカナ（U+30A1 - U+30F6）をひらがなに変換
		if r >= '\u30A1' && r <= '\u30F6' {
			r = r - 0x60
		}
		// 長音記号は除去（必要なら残すよう変更可）
		if r == 'ー' {
			continue
		}
		b.WriteRune(r)
	}
	return b.String()
}

func convertRecipes(aiRecipes []ai.Recipe, inventory fridge.Inventory) []Recipe {
	// product_name → fridge.Item のマップを構築（表記ゆれを正規化）
	itemByName := make(map[string]fridge.Item, len(inventory.Items))
	for _, item := range inventory.Items {
		key := normalizeName(item.ProductName)
		itemByName[key] = item
	}

	result := make([]Recipe, 0, len(aiRecipes))
	for _, r := range aiRecipes {
		ingredients := make([]Ingredient, 0, len(r.Ingredients))
		for _, ing := range r.Ingredients {
			apiIng := Ingredient{
				Name:       ing.Name,
				Amount:     ing.Amount,
				IsInFridge: ing.IsInFridge,
			}
			if ing.IsInFridge {
				if item, ok := itemByName[normalizeName(ing.Name)]; ok {
					apiIng.ProductID = item.ProductID
					apiIng.Unit = item.Unit
				}
			}
			ingredients = append(ingredients, apiIng)
		}
		steps := make([]Step, 0, len(r.Steps))
		for _, s := range r.Steps {
			steps = append(steps, Step{Order: s.Order, Description: s.Description})
		}
		result = append(result, Recipe{
			Name:        r.Name,
			URL:         r.URL,
			Description: r.Description,
			MatchScore:  r.MatchScore,
			Ingredients: ingredients,
			Steps:       steps,
		})
	}
	return result
}

// --- ヘルパー ---

func writeJSON(w http.ResponseWriter, status int, v interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func writeError(w http.ResponseWriter, status int, code, message, details string) {
	writeJSON(w, status, ErrorResponse{
		Error:   message,
		Code:    code,
		Details: details,
	})
	// ログにもエラーを出力
	slog.Error("API error",
		"status", status,
		"code", code,
		"message", message,
		"details", details,
	)
}
