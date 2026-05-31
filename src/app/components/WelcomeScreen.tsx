import { Camera, Receipt, Package, ChefHat, TrendingDown, Sparkles } from 'lucide-react';

interface WelcomeScreenProps {
  onStart: () => void;
}

export function WelcomeScreen({ onStart }: WelcomeScreenProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 p-4">
      <div className="w-full max-w-2xl rounded-2xl bg-white p-8 shadow-2xl">
        <div className="mb-6 text-center">
          <div className="mb-4 flex justify-center">
            <div className="rounded-full bg-gradient-to-r from-blue-500 to-green-500 p-4">
              <Camera className="size-12 text-white" />
            </div>
          </div>
          <h1 className="mb-2 text-4xl font-bold text-gray-800">
            家計簿 & レシピ提案
          </h1>
          <p className="text-lg text-gray-600">
            カメラで簡単に家計と在庫を管理
          </p>
        </div>

        <div className="mb-8 space-y-4">
          <div className="flex items-start gap-4 rounded-lg bg-blue-50 p-4">
            <div className="flex-shrink-0 rounded-full bg-blue-500 p-2">
              <Receipt className="size-6 text-white" />
            </div>
            <div>
              <h3 className="mb-1 font-bold text-gray-800">📸 レシート撮影で自動記録</h3>
              <p className="text-sm text-gray-600">
                レシートをカメラで撮影するだけで、支出と在庫が自動的に記録されます
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-lg bg-green-50 p-4">
            <div className="flex-shrink-0 rounded-full bg-green-500 p-2">
              <Package className="size-6 text-white" />
            </div>
            <div>
              <h3 className="mb-1 font-bold text-gray-800">📦 在庫管理</h3>
              <p className="text-sm text-gray-600">
                家にある食材を一覧で管理。賞味期限も記録できます
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-lg bg-purple-50 p-4">
            <div className="flex-shrink-0 rounded-full bg-purple-500 p-2">
              <ChefHat className="size-6 text-white" />
            </div>
            <div>
              <h3 className="mb-1 font-bold text-gray-800">🍳 レシピ提案</h3>
              <p className="text-sm text-gray-600">
                在庫の食材から作れる料理を自動提案。好みに合わせたレシピが見つかります
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4 rounded-lg bg-orange-50 p-4">
            <div className="flex-shrink-0 rounded-full bg-orange-500 p-2">
              <TrendingDown className="size-6 text-white" />
            </div>
            <div>
              <h3 className="mb-1 font-bold text-gray-800">💰 価格比較</h3>
              <p className="text-sm text-gray-600">
                複数の店舗の価格を比較して、最適な購入場所を提案します
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={onStart}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-blue-500 to-green-500 px-6 py-4 text-lg font-medium text-white shadow-lg transition-all hover:from-blue-600 hover:to-green-600 hover:shadow-xl active:scale-95"
        >
          <Sparkles className="size-6" />
          始める
        </button>
      </div>
    </div>
  );
}
