package ai

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"log/slog"
	"sync"
	"time"

	"github.com/openai/openai-go"
	"github.com/openai/openai-go/option"
	"github.com/openai/openai-go/responses"
)

// Client はAIへのレシピ提案依頼インターフェース
type Client interface {
	SuggestRecipes(ctx context.Context, req SuggestRequest) ([]Recipe, error)
}

type openaiClient struct {
	client       *openai.Client
	model        string
	cache        *responseCache
	cacheEnabled bool
}

// NewOpenAIClient は OpenAI API を使う Client を返す
func NewOpenAIClient(apiKey, model string, cacheEnabled bool) Client {
	c := openai.NewClient(option.WithAPIKey(apiKey))
	return &openaiClient{
		client:       &c,
		model:        model,
		cache:        newResponseCache(10 * time.Minute),
		cacheEnabled: cacheEnabled,
	}
}

func (c *openaiClient) SuggestRecipes(ctx context.Context, req SuggestRequest) ([]Recipe, error) {
	if err := validateSuggestRequest(req); err != nil {
		return nil, err
	}

	if c.cacheEnabled {
		key := cacheKey(req)
		if cached, ok := c.cache.get(key); ok {
			return cached, nil
		}
	}

	recipes, err := c.callAPI(ctx, req)
	if err != nil {
		return nil, err
	}

	if c.cacheEnabled {
		c.cache.set(cacheKey(req), recipes)
	}
	return recipes, nil
}

func (c *openaiClient) callAPI(ctx context.Context, req SuggestRequest) ([]Recipe, error) {
	userMsg := BuildUserMessage(req)
	sysPrompt := BuildSystemPrompt()

	resp, err := c.client.Responses.New(ctx, responses.ResponseNewParams{
		Model:        openai.ResponsesModel(c.model),
		Instructions: openai.String(sysPrompt),
		Input:        responses.ResponseNewParamsInputUnion{OfString: openai.String(userMsg)},
		Reasoning: openai.ReasoningParam{
			Effort: openai.ReasoningEffortMedium,
		},
		Tools: []responses.ToolUnionParam{
			responses.ToolParamOfWebSearchPreview(responses.WebSearchToolTypeWebSearchPreview),
		},
	})
	if err != nil {
		return nil, fmt.Errorf("openai API call failed: %w", err)
	}
	slog.Info("openai API call succeeded",
		"model", resp.Model,
		"input_tokens", resp.Usage.InputTokens,
		"output_tokens", resp.Usage.OutputTokens,
		"total_tokens", resp.Usage.TotalTokens,
	)

	rawText := resp.OutputText()
	if rawText == "" {
		return nil, fmt.Errorf("openai API returned empty response")
	}

	recipes, err := ParseRecipeSuggestions(rawText)
	if err != nil {
		return nil, fmt.Errorf("recipe parse failed: %w", err)
	}
	return recipes, nil
}

func validateSuggestRequest(req SuggestRequest) error {
	if len(req.AdditionalNotes) > 1000 {
		return fmt.Errorf("additionalNotes exceeds maximum length of 1000 characters")
	}
	return nil
}

// cacheKey は SuggestRequest の内容からキャッシュキーを生成する
func cacheKey(req SuggestRequest) string {
	data, _ := json.Marshal(req)
	sum := sha256.Sum256(data)
	return fmt.Sprintf("%x", sum)
}

// --- インメモリキャッシュ ---

type cacheEntry struct {
	recipes   []Recipe
	expiresAt time.Time
}

type responseCache struct {
	mu      sync.RWMutex
	entries map[string]cacheEntry
	ttl     time.Duration
}

func newResponseCache(ttl time.Duration) *responseCache {
	return &responseCache{
		entries: make(map[string]cacheEntry),
		ttl:     ttl,
	}
}

func (rc *responseCache) get(key string) ([]Recipe, bool) {
	rc.mu.RLock()
	defer rc.mu.RUnlock()
	entry, ok := rc.entries[key]
	if !ok || time.Now().After(entry.expiresAt) {
		return nil, false
	}
	return entry.recipes, true
}

func (rc *responseCache) set(key string, recipes []Recipe) {
	rc.mu.Lock()
	defer rc.mu.Unlock()
	rc.entries[key] = cacheEntry{
		recipes:   recipes,
		expiresAt: time.Now().Add(rc.ttl),
	}
}
