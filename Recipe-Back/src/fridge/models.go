package fridge

import "time"

// Item は冷蔵庫の食材1品
type Item struct {
	Name        string `json:"item"`
	Num         int    `json:"num"`
	Amount      int    `json:"amount"`
	Total       int    `json:"total"`
	Date        int    `json:"date"`        // yyyymmdd形式
	Ingredients int    `json:"ingredients"` // 1=野菜, 2=肉/魚, 3=調味料
}

// Inventory は冷蔵庫の在庫全体
type Inventory struct {
	Items     []Item    `json:"items"`
	FetchedAt time.Time `json:"fetchedAt"`
}
