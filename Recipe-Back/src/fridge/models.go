package fridge

import "time"

// Item は冷蔵庫の食材1品（GET /inventory/batches のレスポンス）
type Item struct {
	BatchID         int    `json:"batch_id"`
	ProductID       int    `json:"product_id"`
	ProductName     string `json:"product_name"`
	InitialQuantity string `json:"initial_quantity"`
	CurrentQuantity string `json:"current_quantity"`
	Unit            string `json:"unit"`
	LocationID      int    `json:"location_id"`
	LocationName    string `json:"location_name"`
	PurchasedAt     string `json:"purchased_at"`
	ExpiresAt       string `json:"expires_at"`
	Status          string `json:"status"`
	ReceiptItemID   int    `json:"receipt_item_id"`
}

// Inventory は冷蔵庫の在庫全体
type Inventory struct {
	Items     []Item    `json:"items"`
	FetchedAt time.Time `json:"fetchedAt"`
}

// MovementRequest は POST /inventory/movements のリクエストボディ
type MovementRequest struct {
	ProductID      int    `json:"product_id"`
	MovementType   string `json:"movement_type"`
	Quantity       string `json:"quantity"`
	Unit           string `json:"unit"`
	BatchID        *int   `json:"batch_id"`
	LocationID     *int   `json:"location_id"`
	Reason         string `json:"reason"`
	OccurredAt     string `json:"occurred_at"`
	IdempotencyKey string `json:"idempotency_key"`
}
