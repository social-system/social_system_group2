package fridge

import (
	"context"
	"log/slog"
	"time"
)

type stubClient struct{}

// NewStubClient はデバッグ用のスタブClientを返す
func NewStubClient() Client {
	return &stubClient{}
}

func (s *stubClient) GetInventory(_ context.Context) (Inventory, error) {
	return stubInventory(), nil
}

func (s *stubClient) PostMovement(_ context.Context, req MovementRequest) error {
	slog.Info("stub: PostMovement called", "product_id", req.ProductID, "quantity", req.Quantity, "unit", req.Unit)
	return nil
}

func stubInventory() Inventory {
	return Inventory{
		Items: []Item{
			{BatchID: 1, ProductID: 1, ProductName: "豚肉", InitialQuantity: "300.00", CurrentQuantity: "300.00", Unit: "g", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-04-15", ExpiresAt: "2026-04-22", Status: "active", ReceiptItemID: 1},
			{BatchID: 2, ProductID: 2, ProductName: "長ネギ", InitialQuantity: "2.00", CurrentQuantity: "2.00", Unit: "本", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-06-20", ExpiresAt: "2026-06-30", Status: "active", ReceiptItemID: 2},
			{BatchID: 3, ProductID: 3, ProductName: "にんじん", InitialQuantity: "3.00", CurrentQuantity: "3.00", Unit: "本", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-05-20", ExpiresAt: "2026-05-30", Status: "active", ReceiptItemID: 3},
			{BatchID: 4, ProductID: 4, ProductName: "ジャガイモ", InitialQuantity: "3.00", CurrentQuantity: "3.00", Unit: "個", LocationID: 2, LocationName: "常温", PurchasedAt: "2026-05-20", ExpiresAt: "2026-05-30", Status: "active", ReceiptItemID: 4},
			{BatchID: 5, ProductID: 5, ProductName: "バター", InitialQuantity: "200.00", CurrentQuantity: "200.00", Unit: "g", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-04-10", ExpiresAt: "2026-04-22", Status: "active", ReceiptItemID: 5},
			{BatchID: 6, ProductID: 6, ProductName: "牛乳", InitialQuantity: "1000.00", CurrentQuantity: "150.00", Unit: "ml", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-04-20", ExpiresAt: "2026-04-25", Status: "active", ReceiptItemID: 6},
			{BatchID: 7, ProductID: 7, ProductName: "豆腐", InitialQuantity: "2.00", CurrentQuantity: "2.00", Unit: "丁", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-04-22", ExpiresAt: "2026-04-25", Status: "active", ReceiptItemID: 7},
			{BatchID: 8, ProductID: 8, ProductName: "卵", InitialQuantity: "10.00", CurrentQuantity: "6.00", Unit: "個", LocationID: 1, LocationName: "冷蔵", PurchasedAt: "2026-04-28", ExpiresAt: "2026-05-05", Status: "active", ReceiptItemID: 8},
		},
		FetchedAt: time.Now(),
	}
}
