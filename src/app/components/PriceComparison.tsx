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
  const analyzePrices = (): ItemPriceData[] => {
    if (!expenses || !Array.isArray(expenses)) return [];
    const itemMap = new Map<string, ItemPriceData>();

    expenses.forEach((expense) => {
      // items 配列がない、または空の場合はスキップ
      if (!expense.items || !Array.isArray(expense.items) || expense.items.length === 0) return;

      // 手動在庫追加などのシステムダミーデータ、または店舗名が割り出せない説明文はスキップ
      if (expense.description === "手動在庫追加" || expense.description === "手動登録商品") return;

      // 説明欄（description）に「〜での買い物」や店舗名が入っているため、それを店舗名として利用
      // もし空なら「一般的な店舗」とする
      const detectedStoreName = expense.description 
        ? expense.description.replace('での買い物', '').trim() 
        : '不明な店舗';

      expense.items.forEach((item) => {
        // App.tsx の仕様に合わせて item.raw_name を取得
        const name = item.raw_name || '不明な食材';
        
        // 🚨 【価格比較ガード】「手動一括」や「詳細未入力」などのダミー明細は集計から完全に除外する
        if (
          name.includes("手動一括") || 
          name.includes("詳細未入力") || 
          name.includes("買い物") ||
          name === "a"
        ) {
          return; // 該当した場合はこの明細をスキップ
        }

        const itemNameLower = name.toLowerCase();
        
        // 数量・単位・合計金額の取得 (App.tsx のプロパティ名に完全準拠)
        const quantity = item.purchased_quantity || 1;
        const unit = item.purchased_unit || '個';
        const totalPrice = item.line_total || expense.amount || 0;
        
        // 1つあたりの単価を計算 (item.unit_price があれば最優先、なければ計算)
        const unitPrice = item.unit_price || (totalPrice / quantity);

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

  // 店舗別のおすすめ度を計算
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
      .sort((a, b) => b.percentage - a.percentage);
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
                    {store.bestItemsCount}/{store.totalItems}品目で最安値 ({store.percentage}%)
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

          {/* 検索欄 
          <div className="relative mb-2">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="食材名で検索..."
              className="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-9 pr-8 text-sm text-gray-800 outline-none transition-all focus:border-orange-400 focus:bg-white focus:ring-2 focus:ring-orange-100"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                aria-label="クリア"
              >
                <X className="size-4" />
              </button>
            )}
          </div>

          {/* 件数 
          {searchQuery && (
            <p className="mb-2 text-xs text-gray-500">
              {priceData.length > 0
                ? `「${searchQuery}」: ${priceData.length}件`
                : `「${searchQuery}」に一致する食材はありません`}
            </p>
          )} */}

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
                  <p className="font-bold">{store.storeName}</p>
                </div>
                <p className="text-sm text-orange-100">
                  {store.bestItemsCount}/{store.totalItems}品目で最安値
                </p>
                <p className="text-lg font-bold">{store.percentage}%</p>
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