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
			{Name: "豚肉", Num: 1, Amount: 300, Total: 300, Date: 20260422, Ingredients: 2},
			{Name: "長ネギ", Num: 2, Amount: 100, Total: 200, Date: 20260630, Ingredients: 1},
			{Name: "にんじん", Num: 3, Amount: 80, Total: 240, Date: 20260530, Ingredients: 1},
			{Name: "ジャガイモ", Num: 3, Amount: 120, Total: 360, Date: 20260530, Ingredients: 1},
			{Name: "バター", Num: 1, Amount: 200, Total: 200, Date: 20260422, Ingredients: 3},
			{Name: "牛乳", Num: 1, Amount: 150, Total: 150, Date: 20260425, Ingredients: 3},
			{Name: "豆腐", Num: 2, Amount: 100, Total: 200, Date: 20260425, Ingredients: 1},
			{Name: "卵", Num: 6, Amount: 30, Total: 180, Date: 20260505, Ingredients: 1},
		},
		FetchedAt: time.Now(),
	}
}
