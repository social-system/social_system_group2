package fridge

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"net/http"
	"time"
)

// Client は冷蔵庫在庫管理システムとのインターフェース
type Client interface {
	GetInventory(ctx context.Context) (Inventory, error)
	PostMovement(ctx context.Context, req MovementRequest) error
}

type httpClient struct {
	baseURL    string
	httpClient *http.Client
}

// NewHTTPClient は FRIDGE_API_BASE_URL に接続するHTTPクライアントを返す
func NewHTTPClient(baseURL string) Client {
	return &httpClient{
		baseURL: baseURL,
		httpClient: &http.Client{
			Timeout: 5 * time.Second,
		},
	}
}

// GetInventory は冷蔵庫システムから在庫を取得する。
// システムが利用不可の場合はエラーにせず空のInventoryを返す（グレースフルデグラデーション）。
func (c *httpClient) GetInventory(ctx context.Context) (Inventory, error) {
	url := c.baseURL + "/inventory/batches"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		slog.Warn("fridge request creation failed, using stub data", "error", err)
		return stubInventory(), nil
	}

	resp, err := c.httpClient.Do(req)
	if err != nil {
		slog.Warn("fridge system unavailable, using stub data", "error", err)
		return stubInventory(), nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		slog.Warn("fridge system returned non-200, using stub data", "status", resp.StatusCode)
		return stubInventory(), nil
	}

	var inventory Inventory
	if err := json.NewDecoder(resp.Body).Decode(&inventory); err != nil {
		return Inventory{}, fmt.Errorf("fridge inventory decode failed: %w", err)
	}
	inventory.FetchedAt = time.Now()
	return inventory, nil
}

// PostMovement は冷蔵庫システムに在庫移動（消費）を記録する。
func (c *httpClient) PostMovement(ctx context.Context, req MovementRequest) error {
	body, err := json.Marshal(req)
	if err != nil {
		return fmt.Errorf("movement request marshal failed: %w", err)
	}

	url := c.baseURL + "/inventory/movements"
	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("movement request creation failed: %w", err)
	}
	httpReq.Header.Set("Content-Type", "application/json")

	resp, err := c.httpClient.Do(httpReq)
	if err != nil {
		return fmt.Errorf("movement request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("inventory movements returned status %d", resp.StatusCode)
	}
	return nil
}
