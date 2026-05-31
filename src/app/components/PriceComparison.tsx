import { useState } from 'react';
import { TrendingDown, Store, Award, AlertCircle, Search, X } from 'lucide-react';
// App.tsx から必要な型のみをインポート
import type { Expense } from '../App';

interface PriceComparisonProps {
  expenses: Expense[];
  compact?: boolean;
}

interface ItemPriceData {
  itemName: string;
  stores: {
    storeName: string;
    price: number;
    unitPrice: number;
    quantity: number;
    unit: string;
    date: Date;
  }[];
  bestStore: string;
  bestPrice: number;
}

export function PriceComparison({ expenses, compact = false }: PriceComparisonProps) {
  const [searchQuery, setSearchQuery] = useState('');

  // 商品別に価格データを集計
// 商品別に価格データを集計
  const analyzePrices = (): ItemPriceData[] => {
    if (!expenses || !Array.isArray(expenses)) return [];
    const itemMap = new Map<string, ItemPriceData>();

    expenses.forEach((expense) => {
      // items 配列がない、または空の場合はスキップ
      if (!expense.items || !Array.isArray(expense.items) || expense.items.length === 0) return;

      const rawDescription = String(expense.description || "").trim();

      // 💡【修正ガード1】店舗名に「手動在庫追加」や「手動登録商品」が含まれるレシートは完全にスキップ
      if (
        rawDescription.includes("手動在庫追加") || 
        rawDescription.includes("手動登録商品")
      ) {
        return;
      }

      // 説明欄（description）に「〜での買い物」や店舗名が入っているため、それを店舗名として利用
      const detectedStoreName = expense.description 
        ? expense.description.replace('での買い物', '').replace('【手動】', '').trim() 
        : '不明な店舗';

      // 💡【追加ガード】整形後の店名が「手動在庫追加」になってしまった場合もスキップ
      if (detectedStoreName === "手動在庫追加") {
        return;
      }

      expense.items.forEach((item) => {
        const name = item.raw_name || '不明な食材';
        
        // 【価格比較ガード】ダミー明細は集計から完全に除外する
        if (
          name.includes("手動一括") || 
          name.includes("詳細未入力") || 
          name.includes("買い物") ||
          name === "a"
        ) {
          return; 
        }

        const itemNameLower = name.toLowerCase();
        
        // 数量・単位・合計金額の取得
        const quantity = item.purchased_quantity || 1;
        const unit = item.purchased_unit || '個';
        const totalPrice = item.line_total || expense.amount || 0;
        
        // 1つあたりの単価を計算
        const unitPrice = item.unit_price || (totalPrice / quantity);

        // 💡【修正ガード2】単価が0円以下のデータ（手動登録による0円など）は価格比較に含めずスキップ
        if (unitPrice <= 0) {
          return;
        }

        if (!itemMap.has(itemNameLower)) {
          itemMap.set(itemNameLower, {
            itemName: name,
            stores: [],
            bestStore: '',
            bestPrice: Infinity,
          });
        }

        const data = itemMap.get(itemNameLower)!;
        data.stores.push({
          storeName: detectedStoreName,
          price: totalPrice,
          unitPrice: unitPrice,
          quantity: quantity,
          unit: unit,
          date: expense.date,
        });

        // 最安値を更新
        if (unitPrice < data.bestPrice) {
          data.bestPrice = unitPrice;
          data.bestStore = detectedStoreName;
        }
      });
    });

    return Array.from(itemMap.values()).sort((a, b) => a.itemName.localeCompare(b.itemName));
  };

  // 店舗別のおすすめ度を計算 (最安値の品目数が多い順に並び替え)
  const getStoreRecommendations = () => {
    const storeScores = new Map<string, { bestItemsCount: number; totalItems: number }>();

    const priceData = analyzePrices();
    priceData.forEach((item) => {
      item.stores.forEach((store) => {
        if (!storeScores.has(store.storeName)) {
          storeScores.set(store.storeName, { bestItemsCount: 0, totalItems: 0 });
        }
        const score = storeScores.get(store.storeName)!;
        score.totalItems++;
        if (store.storeName === item.bestStore) {
          score.bestItemsCount++;
        }
      });
    });

    return Array.from(storeScores.entries())
      .map(([storeName, { bestItemsCount, totalItems }]) => ({
        storeName,
        bestItemsCount,
        totalItems,
        percentage: Math.round((bestItemsCount / totalItems) * 100),
      }))
      .sort((a, b) => {
        // 1. まず最安値の「品目数（件数）」で比較 (多い順)
        if (b.bestItemsCount !== a.bestItemsCount) {
          return b.bestItemsCount - a.bestItemsCount;
        }
        // 2. 品目数が全く同じなら、「最安値の割合（％）」で比較 (高い順)
        return b.percentage - a.percentage;
      });
  };

  const allPriceData = analyzePrices();
  const storeRecommendations = getStoreRecommendations();
  
  const priceData = searchQuery.trim()
    ? allPriceData.filter((item) =>
        item.itemName.toLowerCase().includes(searchQuery.toLowerCase()),
      )
    : allPriceData;
  

  if (priceData.length === 0) {
    return (
      <div className="rounded-lg bg-white p-4 shadow-md">
        <div className="mb-3 flex items-center gap-2">
          <TrendingDown className="size-5 text-orange-500" />
          <h3 className="text-lg font-bold text-gray-800">価格比較</h3>
        </div>
        <div className="py-8 text-center text-gray-400">
          <AlertCircle className="mx-auto mb-2 size-10" />
          <p className="text-sm">店舗名と商品明細が記録されているデータがありません</p>
          <p className="mt-1 text-xs">レシート撮影や手動入力を行うと価格比較ができます</p>
        </div>
      </div>
    );
  }

  if (compact) {
    // コンパクト版（サイドバー表示用）
    return (
      <div className="space-y-4">
        {/* おすすめ店舗 */}
        {storeRecommendations.length > 0 && (
          <div className="rounded-lg bg-gradient-to-br from-orange-500 to-yellow-500 p-4 text-white shadow-md">
            <div className="mb-3 flex items-center gap-2">
              <Award className="size-5" />
              <h3 className="font-bold">おすすめの店舗</h3>
            </div>
            <div className="space-y-2">
              {storeRecommendations.slice(0, 3).map((store, idx) => (
                <div
                  key={store.storeName}
                  className="rounded-lg bg-white/20 p-3 backdrop-blur"
                >
                  <div className="mb-1 flex items-center gap-2">
                    {idx === 0 && <span className="text-lg">🥇</span>}
                    {idx === 1 && <span className="text-lg">🥈</span>}
                    {idx === 2 && <span className="text-lg">🥉</span>}
                    <p className="text-sm font-bold">{store.storeName}</p>
                  </div>
                  <p className="text-xs text-orange-100">
                    最安値: <span className="font-bold text-white">{store.bestItemsCount}</span>品目 / 全{store.totalItems}品中 ({store.percentage}%)
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 商品別価格比較 */}
        <div className="rounded-lg bg-white p-4 shadow-md">
          <div className="mb-2 flex items-center gap-2">
            <TrendingDown className="size-5 text-orange-500" />
            <h3 className="font-bold text-gray-800">商品別価格</h3>
          </div>

          {/* リスト */}
          <div className="max-h-[500px] space-y-3 overflow-y-auto">
            {priceData.map((item) => (
              <div
                key={item.itemName}
                className="rounded-lg border border-gray-200 p-3 transition-all hover:border-orange-300"
              >
                <div className="mb-2 flex items-center justify-between">
                  <p className="font-medium text-gray-800">{item.itemName}</p>
                  <p className="text-xs font-bold text-orange-600">
                    ¥{item.bestPrice.toFixed(0)}/{item.stores[0]?.unit || '個'}
                  </p>
                </div>

                <div className="space-y-1">
                  {item.stores
                    .sort((a, b) => a.unitPrice - b.unitPrice)
                    .slice(0, 3)
                    .map((store, idx) => {
                      const isBest = store.storeName === item.bestStore;
                      return (
                        <div
                          key={`${store.storeName}-${idx}`}
                          className={`flex items-center justify-between rounded p-2 text-xs ${
                            isBest ? 'bg-orange-50' : 'bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center gap-1">
                            <Store className="size-3 text-gray-500" />
                            <span className="font-medium text-gray-700">
                              {store.storeName}
                            </span>
                            {isBest && (
                              <span className="ml-1 rounded bg-orange-500 px-1 py-0.5 text-[10px] font-bold text-white">
                                最安
                              </span>
                            )}
                          </div>
                          <span className="font-bold text-gray-800">
                            ¥{store.unitPrice.toFixed(0)}
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // フル版（通常表示用）
  return (
    <div className="space-y-4">
      {/* おすすめ店舗 */}
      {storeRecommendations.length > 0 && (
        <div className="rounded-lg bg-gradient-to-r from-orange-500 to-yellow-500 p-6 text-white shadow-md">
          <div className="mb-3 flex items-center gap-2">
            <Award className="size-6" />
            <h3 className="text-xl font-bold">おすすめの店舗</h3>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {storeRecommendations.slice(0, 3).map((store, idx) => (
              <div
                key={store.storeName}
                className="rounded-lg bg-white/20 p-4 backdrop-blur"
              >
                <div className="mb-2 flex items-center gap-2">
                  {idx === 0 && <span className="text-2xl">🥇</span>}
                  {idx === 1 && <span className="text-2xl">🥈</span>}
                  {idx === 2 && <span className="text-2xl">🥉</span>}
                  <p className="font-bold text-lg">{store.storeName}</p>
                </div>
                <p className="text-sm text-orange-500 bg-white rounded px-2 py-1 font-bold inline-block mb-2">
                  最安値: {store.bestItemsCount} 品目
                </p>
                <p className="text-xs text-orange-100">
                  （この店の取扱品目のうち {store.percentage}% が最安値）
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 商品別価格比較 */}
      <div className="rounded-lg bg-white p-6 shadow-md">
        <div className="mb-4 flex items-center gap-2">
          <TrendingDown className="size-6 text-orange-500" />
          <h2 className="text-2xl font-bold text-gray-800">商品別価格比較</h2>
        </div>

        <div className="space-y-4">
          {priceData.map((item) => (
            <div
              key={item.itemName}
              className="rounded-lg border border-gray-200 p-4 transition-all hover:border-orange-300 hover:shadow-md"
            >
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-800">{item.itemName}</h3>
                <div className="text-right">
                  <p className="text-xs text-gray-500">最安値</p>
                  <p className="text-sm font-bold text-orange-600">
                    ¥{item.bestPrice.toFixed(0)}/{item.stores[0]?.unit || '個'}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                {item.stores
                  .sort((a, b) => a.unitPrice - b.unitPrice)
                  .map((store, idx) => {
                    const isBest = store.storeName === item.bestStore;
                    const priceDiff = store.unitPrice - item.bestPrice;
                    const percentDiff = item.bestPrice > 0 ? Math.round((priceDiff / item.bestPrice) * 100) : 0;

                    return (
                      <div
                        key={`${store.storeName}-${idx}`}
                        className={`flex items-center justify-between rounded-lg p-3 ${
                          isBest
                            ? 'bg-orange-50 border border-orange-300'
                            : 'bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <Store className="size-4 text-gray-500" />
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-medium text-gray-800">
                                {store.storeName}
                              </p>
                              {isBest && (
                                <span className="rounded bg-orange-500 px-2 py-0.5 text-xs font-bold text-white">
                                  最安値
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500">
                              {store.quantity}
                              {store.unit} - ¥{store.price}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-800">
                            ¥{store.unitPrice.toFixed(0)}/{store.unit}
                          </p>
                          {!isBest && priceDiff > 0 && (
                            <p className="text-xs text-red-600">
                              +¥{priceDiff.toFixed(0)} (+{percentDiff}%)
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}