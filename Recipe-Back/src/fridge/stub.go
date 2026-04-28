package fridge

import (
	"context"
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

func stubInventory() Inventory {
	return Inventory{
		Items: []Item{
			{Name: "豚肉", Amount: "200g", ExpiryDate: time.Date(2026, 4, 22, 0, 0, 0, 0, time.Local), Category: "肉"},
			{Name: "長ネギ", Amount: "100g", ExpiryDate: time.Date(2026, 6, 30, 0, 0, 0, 0, time.Local), Category: "野菜"},
			{Name: "にんじん", Amount: "1本", ExpiryDate: time.Date(2026, 5, 30, 0, 0, 0, 0, time.Local), Category: "野菜"},
			{Name: "ジャガイモ", Amount: "3個", ExpiryDate: time.Date(2026, 5, 30, 0, 0, 0, 0, time.Local), Category: "野菜"},
			{Name: "バター", Amount: "120g", ExpiryDate: time.Date(2026, 4, 22, 0, 0, 0, 0, time.Local), Category: "乳製品"},
			{Name: "牛乳", Amount: "300ml", ExpiryDate: time.Date(2026, 4, 25, 0, 0, 0, 0, time.Local), Category: "乳製品"},
			{Name: "豆腐", Amount: "150g", ExpiryDate: time.Date(2026, 4, 25, 0, 0, 0, 0, time.Local), Category: "豆腐"},
			{Name: "卵", Amount: "6個", ExpiryDate: time.Date(2026, 5, 5, 0, 0, 0, 0, time.Local), Category: "卵"},
		},
		FetchedAt: time.Now(),
	}
}
