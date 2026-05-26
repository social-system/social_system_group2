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

	var movementsCreated int
	var skipped []string

	now := time.Now()
	for _, ing := range req.Ingredients {
		if !ing.IsInFridge || ing.ProductID == 0 {
			continue
		}

		quantity, parsedUnit := parseAmount(ing.Amount)
		unit := ing.Unit
		if unit == "" {
			unit = parsedUnit
		}

		movReq := fridge.MovementRequest{
			ProductID:      ing.ProductID,
			MovementType:   "consume",
			Quantity:       quantity,
			Unit:           unit,
			BatchID:        nil,
			LocationID:     nil,
			Reason:         fmt.Sprintf("レシピで使用: %s", req.RecipeName),
			OccurredAt:     now.Format("2006-01-02T15:04:05"),
			IdempotencyKey: fmt.Sprintf("recipe:consume:%d:%d", ing.ProductID, now.UnixNano()),
		}

		if err := h.fridgeClient.PostMovement(r.Context(), movReq); err != nil {
			slog.Warn("inventory movement failed", "product_id", ing.ProductID, "name", ing.Name, "error", err)
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

var numericRe = regexp.MustCompile(`^(\d+)(?:/(\d+))?`)

// parseAmount は "200g", "2個", "大さじ2", "1/2個", "適量" などを (quantity, unit) に変換する。
// 数値が抽出できない場合は "1.00" を返す。
func parseAmount(amount string) (quantity string, unit string) {
	amount = strings.TrimSpace(amount)

	// 前置ユニット（大さじ・小さじ）を先に抽出
	for _, prefix := range []string{"大さじ", "小さじ"} {
		if strings.HasPrefix(amount, prefix) {
			rest := strings.TrimPrefix(amount, prefix)
			q, _ := parseAmount(rest)
			return q, prefix
		}
	}

	m := numericRe.FindStringSubmatch(amount)
	if m == nil {
		return "1.00", ""
	}

	numerator, _ := strconv.ParseFloat(m[1], 64)
	val := numerator
	if m[2] != "" {
		denominator, _ := strconv.ParseFloat(m[2], 64)
		if denominator != 0 {
			val = numerator / denominator
		}
	}

	// 数値部分の後ろの文字列をユニットとする（"~N" などは除去）
	after := amount[len(m[0]):]
	if idx := strings.IndexAny(after, "~〜"); idx >= 0 {
		after = ""
	}
	unit = strings.TrimSpace(after)

	return fmt.Sprintf("%.2f", val), unit
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
