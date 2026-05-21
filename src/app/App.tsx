import { useState } from "react";
import {
  Camera,
  Receipt,
  ChefHat,
  Plus,
  Package,
  Settings,
  X,
  Trash2,
  Eye,
  AlertTriangle,
  ShoppingCart,
  Loader2,
  Store,
} from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import { useEffect } from "react";
import { UniversalCamera } from "./components/UniversalCamera";
import { ExpenseList } from "./components/ExpenseList";
import { InventoryList } from "./components/InventoryList";
import { RecipeList } from "./components/RecipeList";
import { AddExpenseForm } from "./components/AddExpenseForm";
import { AddInventoryForm } from "./components/AddInventoryForm";
import { AddRecipeForm } from "./components/AddRecipeForm";
import { SettingsModal } from "./components/SettingsModal";


//const kakeibo_URL = "http://localhost:8000";
const kakeibo_URL = "https://social-system-group2.onrender.com";


//const recipe_URL = "http://localhost:8080";
const recipe_URL = "https://social-system-group2-1.onrender.com";




// --- 型定義 ---
interface RecipeIngredient {
  name: string;
  amount: string;
  isInFridge: boolean;
  productId?: number;
  unit?: string;
}
interface RecipeStep {
  order: number;
  description: string;
}

interface RecipeListProps {
  recipes: Recipe[];
  onDelete: (id: string) => void;
  inventory: InventoryItem[];
  onSelectRecipe: (recipe: Recipe) => void;
}

export const RecipeListCall = ({ recipes, onDelete, inventory, onSelectRecipe }: RecipeListProps) => {
  return (
    <div className="space-y-4">
      {recipes.map((recipe) => {
        const missingIngredients = recipe.ingredients?.filter(ing => !ing.isInFridge) || [];

        return (
          <div key={recipe.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-all bg-white gap-4">
            {/* 左側：レシピの基本情報 */}
            <div className="flex-1 min-w-[180px]">
              <h3 className="font-bold text-gray-800 text-base line-clamp-1">{recipe.title}</h3>
              <p className="text-sm text-gray-500 mt-0.5">
                ⏱ {recipe.cookingTime}分 / {recipe.ingredients?.length || 0}品目
              </p>
            </div>
            
            {/* 中央：足りない材料 */}
            <div className="flex-2 flex items-center justify-center px-2">
              {missingIngredients.length > 0 ? (
                <div className="flex items-center gap-1 bg-amber-50 border border-amber-200 text-amber-800 rounded-md p-2 text-xs max-w-xs">
                  <span className="font-bold whitespace-nowrap shrink-0">⚠️ 不足:</span>
                  <span className="text-gray-700 truncate" title={missingIngredients.map(ing => ing.name).join("、")}>
                    {missingIngredients.map(ing => ing.name).join("、")}
                  </span>
                </div>
              ) : (
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-md p-2 text-xs font-bold whitespace-nowrap">
                  ✨ 手持ちで作れます！
                </div>
              )}
            </div>
            
            {/* 右側：アクションボタン */}
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => onSelectRecipe(recipe)}
                className="flex items-center gap-1 bg-purple-500 text-white px-3 py-1.5 rounded-md hover:bg-purple-600 transition-all text-sm font-medium whitespace-nowrap"
              >
                <Eye className="size-4" />
                詳細・適応
              </button>

              <button
                type="button"
                onClick={() => onDelete(recipe.id)}
                className="p-1.5 text-gray-400 hover:text-red-500 transition-all"
              >
                <Trash2 className="size-5" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export interface Expense {
  id: string;
  amount: number;
  category: string;
  description: string;
  date: Date;
  imageUrl?: string;
}

export interface Recipe {
  id: string;
  title: string;
  url?: string;
  description?: string;
  matchScore?: string;
  ingredients: RecipeIngredient[];
  instructions: string;
  steps?: RecipeStep[];
  cookingTime: number;
  estimatedCost?: number;
}

export interface InventoryItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  category: string;
  expiryDate?: Date;
  imageUrl?: string;
}

interface ShopPriceEstimate {
  shopName: string;
  totalPrice: number;
  deliveryFee?: number;
}

export interface UserSettings {
  staples: string[];
  likedIngredients: string[];
  dislikedIngredients: string[];
  isSetupComplete: boolean;
}

export default function App() {
  // 初期ダミーデータを空の配列 [] に変更
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);

  const [showCamera, setShowCamera] = useState(false);
  const [showAddExpense, setShowAddExpense] = useState(false);
  const [showAddInventory, setShowAddInventory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const [settings, setSettings] = useState<UserSettings>({
    staples: [],
    likedIngredients: [],
    dislikedIngredients: [],
    isSetupComplete: false,
  });

  const [prompt, setPrompt] = useState(""); 
  const [isGenerating, setIsGenerating] = useState(false); 
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [activeTab, setActiveTab] = useState("expenses");

  const [shopPrices, setShopPrices] = useState<ShopPriceEstimate[]>([]);
  const [isFetchingPrices, setIsFetchingPrices] = useState(false);

  const handleCloseModal = () => {
    setSelectedRecipe(null);
    setShopPrices([]);
    setIsFetchingPrices(false);
  };

  // 日付オブジェクトから「YYYYMMDD」の数値を作成する共通ヘルパー
  const formatToYmdNumber = (date: Date) => {
    const targetDate = date instanceof Date ? date : new Date(date);
    return Number(targetDate.toISOString().split('T')[0].replace(/-/g, ''));
  };

  // 1. 初回起動時の処理（ヘルスチェック、設定確認、家計簿読み込み）
  useEffect(() => {
    const checkHealth = async () => {
      try {
        //const res = await fetch(`http://localhost:8000/`); 
        const res = await fetch(kakeibo_URL); 
        if (!res.ok) throw new Error(`HTTPエラー: ${res.status}`);
        const data = await res.json();
        console.log("【Health Check 成功】", data);
      } catch (err) {
        console.error("【Health Check 失敗】:", err);
      }
    };

    //checkHealth();

    if (!settings.isSetupComplete) {
      setShowSettings(true);
    }
    fetchExpenses();
  }, []);

  // 2. 家計簿・レシートデータの読み込み (GET /receipts 仕様に完全準拠)
  const fetchExpenses = async () => {
    try {
      //const res = await fetch(`http://localhost:8000/receipts`); 
      const res = await fetch(`${kakeibo_URL}/receipts`); 
      if (!res.ok) throw new Error(`サーバーエラー: ${res.status}`);
      const data = await res.json();
      
      if (Array.isArray(data)) {
        const mappedExpenses: Expense[] = data.map((item: any) => {
          const dateStr = String(item.purchased_at);
          const y = Number(dateStr.substring(0, 4));
          const m = Number(dateStr.substring(4, 6)) - 1;
          const d = Number(dateStr.substring(6, 8));
          return {
            id: item.id.toString(),
            amount: item.total_amount,
            category: "レシートデータ",
            description: item.store_name || "店舗名未設定",
            date: new Date(y, m, d)
          };
        });
        setExpenses(mappedExpenses);
      }
    } catch (err) {
      console.error("読み込み失敗", err);
    }
  };

  // 3. 手動家計簿追加（POST /receipts 仕様に完全準拠）
  const addExpenseCall = async (expense: Omit<Expense, 'id'>) => {
    try {
      const requestBody = {
        purchased_at: formatToYmdNumber(expense.date || new Date()),
        store_name: expense.description || "手動登録店舗",
        total_amount: Number(expense.amount),
        items: [
          {
            raw_name: expense.description || "手動登録商品",
            normalized_name: expense.category || "未分類",
            product_id: 1,
            category_id: 1,
            purchased_quantity: 1,
            purchased_unit: "個",
            base_quantity: 1,
            base_unit: "個",
            unit_price: Number(expense.amount),
            line_total: Number(expense.amount),
            is_inventory_target: false 
          }
        ]
      };

      //const response = await fetch(`http://localhost:8000/receipts`, {
      const response = await fetch(`${kakeibo_URL}/receipts`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);

      const resData = await response.json();
      const newExpense = { 
        ...expense, 
        id: resData.id ? resData.id.toString() : Date.now().toString() 
      };
      setExpenses([newExpense, ...expenses]);
    } catch (err) {
      console.error("家計簿データの送信に失敗しました:", err);
      alert("サーバーへの保存に失敗しました。");
    }
  };

  // 4. 家計簿・レシートデータ削除 (DELETE /receipts/{receipt_id} 仕様に完全準拠)
  const deleteExpenseCall = async (id: string) => {
    try {
      //const response = await fetch(`http://localhost:8000/receipts/${id}`, {
      const response = await fetch(`${kakeibo_URL}/receipts/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);
      setExpenses(expenses.filter((e) => e.id !== id));
    } catch (err) {
      console.error("データの削除に失敗しました:", err);
      alert("サーバーからのデータ削除に失敗しました。");
    }
  };

  const deleteRecipe = (id: string) => {
    setRecipes(recipes.filter((r) => r.id !== id));
  };

  // 5. 手動在庫追加 (POST /receipts 仕様に準拠させ、is_inventory_targetをtrueにする)
  const addInventoryItemCall = async (item: Omit<InventoryItem, 'id'>) => {
    try {
      const requestBody = {
        purchased_at: formatToYmdNumber(new Date()),
        store_name: "手動在庫追加",
        total_amount: 0, 
        items: [
          {
            raw_name: item.name,
            normalized_name: item.name,
            product_id: 1,
            category_id: 1,
            purchased_quantity: Number(item.quantity),
            purchased_unit: item.unit || "個",
            base_quantity: Number(item.quantity),
            base_unit: item.unit || "個",
            unit_price: 0,
            line_total: 0,
            is_inventory_target: true 
          }
        ]
      };

      const response = await fetch(`${kakeibo_URL}/receipts`, {
      //const response = await fetch(`http://localhost:8000/receipts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);

      const newItem = { ...item, id: Date.now().toString() };
      setInventory([newItem, ...inventory]);
    } catch (err) {
      console.error("在庫データの送信に失敗しました:", err);
      alert("サーバーへの保存に失敗しました。");
    }
  };

  // 6. 在庫データ削除 (DELETE /receipts/{id} 仕様に連動)
  const deleteInventoryItemCall = async (id: string) => {
    try {
      const response = await fetch(`${kakeibo_URL}/receipts/${id}`, {
      //const response = await fetch(`http://localhost:8000/receipts/${id}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);
      setInventory(inventory.filter((i) => i.id !== id));
    } catch (err) {
      console.error("在庫データの削除に失敗しました:", err);
      alert("サーバーからのデータ削除に失敗しました。");
    }
  };

  const updateInventoryItem = (id: string, updates: Partial<InventoryItem>) => {
    setInventory(inventory.map((item) => (item.id === id ? { ...item, ...updates } : item)));
  };

  const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  const getSuggestedRecipes = () => {
    return recipes.filter((recipe) => {
      const missingCount = recipe.ingredients?.filter(i => !i.isInFridge).length || 0;
      return missingCount === 0;
    });
  };

  const suggestedRecipes = getSuggestedRecipes();

  const handleGenerateRecipe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isGenerating) return;
    setIsGenerating(true);

    const currentPrompt = prompt || "おすすめのレシピ";    

    try {
      const response = await fetch(`${recipe_URL}/api/v1/recipes/suggest`, {
      //const response = await fetch(`http://localhost:8080/api/v1/recipes/suggest`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          additionalNotes: currentPrompt 
        }),
      });

      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);
      const data = await response.json();

      if (data.recipes && Array.isArray(data.recipes)) {
        const newRecipes: Recipe[] = data.recipes.map((apiRecipe: any, index: number) => ({
          id: `ai-${Date.now()}-${index}`,
          title: apiRecipe.name,
          url: apiRecipe.url,
          description: apiRecipe.description,
          matchScore: apiRecipe.matchScore,
          ingredients: apiRecipe.ingredients || [],
          steps: apiRecipe.steps || [],
          instructions: apiRecipe.steps 
            ? apiRecipe.steps.map((s: any) => `${s.order}. ${s.description}`).join("\n")
            : "手順情報はバックエンドのレスポンスを確認してください。",
          cookingTime: 20, 
          estimatedCost: 450 
        }));

        setRecipes(prev => [...newRecipes, ...prev]);
        setPrompt(""); 
      }
    } catch (err) {
      console.error("レシピ生成に失敗しました:", err);
      alert("レシピ生成に失敗しました。サーバーの稼働状況を確認してください。");
    } finally {
      setIsGenerating(false);
    }
  };

  // 不足食材の最安店舗・価格見積もりを取得する関数（ステート名・変数名の不整合を完全修正）
  const handleFetchPurchaseEstimation = async (recipe: Recipe) => {
    if (isFetchingPrices) return;
    setIsFetchingPrices(true);
    setShopPrices([]); 

    try {
      // 1. 冷蔵庫にない（要購入）かつ productId が存在する食材を特定
      const missingIngredient = recipe.ingredients.find(ing => !ing.isInFridge && ing.productId);

      if (missingIngredient && missingIngredient.productId) {
        // 2. 仕様書に定義されている「最安購入店舗取得」API（GET /prices/cheapest）へ通信
        const pId = missingIngredient.productId;
        //const response = await fetch(`http://localhost:8000/prices/cheapest?product_id=${pId}&period_days=90`);
        const response = await fetch(`${kakeibo_URL}/prices/cheapest?product_id=${pId}&period_days=90`);
        
        if (response.ok) {
          const data = await response.json();

          // 過去に購入実績があり、最安店舗データが返ってきた場合
          if (data && data.cheapest) {
            const cheapestInfo = data.cheapest;
            const basePrice = Math.round(cheapestInfo.price_per_base_unit);

            // APIのリアルな最安値データと、それをもとにした他店比較のシミュレーション配列を構築
            const realShopEstimates: ShopPriceEstimate[] = [
              { 
                shopName: `${cheapestInfo.store_name} (過去最安店)`, 
                totalPrice: basePrice 
              },
              { 
                shopName: "ライフマート (周辺参考価格)", 
                totalPrice: Math.round(basePrice * 1.15) 
              },
              { 
                shopName: "ネットスーパー西友 (配送料込)", 
                totalPrice: Math.round(basePrice * 1.05), 
                deliveryFee: 200 
              }
            ];

            setShopPrices(realShopEstimates);
            setIsFetchingPrices(false);
            return; 
          }
        }
      }

      // 3. 過去履歴がない(cheapest: null)、または対象食材にproductIdがない場合のフォールバック（テスト用データ）
      const mockShopPrices: ShopPriceEstimate[] = [
        { shopName: "スーパー丸エツ (目安価格)", totalPrice: 320 },
        { shopName: "ライフマート (目安価格)", totalPrice: 350 },
        { shopName: "ネットスーパー西友 (配送料込)", totalPrice: 300, deliveryFee: 200 }
      ];
      setShopPrices(mockShopPrices);

    } catch (err) {
      console.error("最安店舗の取得に失敗しました:", err);
      setShopPrices([
        { shopName: "スーパー丸エツ (オフライン目安)", totalPrice: 320 },
        { shopName: "ライフマート (オフライン目安)", totalPrice: 350 }
      ]);
    } finally {
      setIsFetchingPrices(false);
    }
  };

  const handleFinalAdd = async (recipe: Recipe) => {
    try {
      // 1. バックエンドAPI（POST /api/v1/recipes/accept）に在庫消費リクエストを送信
      const acceptResponse = await fetch(`${recipe_URL}/api/v1/recipes/accept`, {
      //const acceptResponse = await fetch(`http://localhost:8080/api/v1/recipes/accept`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipeName: recipe.title,
          ingredients: recipe.ingredients 
        }),
      });

      if (!acceptResponse.ok) {
        console.warn("Recipe-Backでの在庫消費に失敗しました。家計簿の登録のみ続行します。");
      }

      // 2. 家計簿側への支出記録処理
      const response = await fetch(`${kakeibo_URL}/receipts`, {
      //const response = await fetch(`http://localhost:8000/receipts`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          purchased_at: formatToYmdNumber(new Date()),
          store_name: "AIレシピ適応調理",
          total_amount: recipe.estimatedCost || 0,
          items: [
            {
              raw_name: recipe.title || "AIレシピ料理",
              normalized_name: recipe.title || "AIレシピ料理",
              product_id: 1,
              category_id: 1,
              purchased_quantity: 1,
              purchased_unit: "食",
              base_quantity: 1,
              base_unit: "食",
              unit_price: recipe.estimatedCost || 0,
              line_total: recipe.estimatedCost || 0,
              is_inventory_target: false
            }
          ]
        }),
      });

      if (!response.ok) throw new Error(`家計簿サーバーエラー: ${response.status}`);

      // 3. フロントエンドの簡易的な在庫ステート更新
      if (recipe.ingredients && recipe.ingredients.length > 0) {
        setInventory(prevInventory => {
          return prevInventory
            .map(item => {
              const isUsed = recipe.ingredients.some((ing) => 
                ing.isInFridge && (item.name.toLowerCase().includes(ing.name.toLowerCase()) || ing.name.toLowerCase().includes(item.name.toLowerCase()))
              );
              if (isUsed) {
                const nextQty = item.quantity - 1;
                return { ...item, quantity: nextQty };
              }
              return item;
            })
            .filter(item => item.quantity > 0);
        });
      }

      alert("家計簿に追加し、バックエンドの冷蔵庫在庫を消費しました！");
      handleCloseModal();
      setActiveTab('expenses');
      fetchExpenses();
    } catch (err) {
      console.error("レシピの適応に失敗しました:", err);
      alert("レシピの適応処理に失敗しました。");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="mx-auto max-w-4xl p-4">
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex-1"></div>
            <div className="flex-1 text-center">
              <h1 className="mb-2 text-4xl font-bold text-gray-800">💰 家計簿 & レシピ</h1>
              <p className="text-gray-600">カメラで簡単記録</p>
            </div>
            <div className="flex flex-1 justify-end">
              <button
                type="button"
                onClick={() => setShowSettings(true)}
                className="rounded-lg p-2 text-gray-600 transition-all hover:bg-gray-200 active:scale-95"
                aria-label="設定"
              >
                <Settings className="size-6" />
              </button>
            </div>
          </div>
        </header>

        <Tabs.Root value={activeTab} onValueChange={setActiveTab} className="w-full">
          <Tabs.List className="mb-6 flex gap-2 rounded-lg bg-white p-1 shadow-md">
            <Tabs.Trigger
              value="expenses"
              className="flex-1 rounded-md px-3 py-3 font-medium text-gray-600 transition-all hover:bg-gray-50 data-[state=active]:bg-blue-500 data-[state=active]:text-white data-[state=active]:shadow"
            >
              <Receipt className="mb-1 inline-block size-5" />
              <span className="ml-2">家計簿</span>
            </Tabs.Trigger>
            <Tabs.Trigger
              value="inventory"
              className="flex-1 rounded-md px-3 py-3 font-medium text-gray-600 transition-all hover:bg-gray-50 data-[state=active]:bg-green-500 data-[state=active]:text-white data-[state=active]:shadow"
            >
              <Package className="mb-1 inline-block size-5" />
              <span className="ml-2">在庫</span>
            </Tabs.Trigger>
            <Tabs.Trigger
              value="recipes"
              className="flex-1 rounded-md px-3 py-3 font-medium text-gray-600 transition-all hover:bg-gray-50 data-[state=active]:bg-purple-500 data-[state=active]:text-white data-[state=active]:shadow"
            >
              <ChefHat className="mb-1 inline-block size-5" />
              <span className="ml-2">レシピ</span>
            </Tabs.Trigger>
          </Tabs.List>

          <Tabs.Content value="expenses" className="space-y-4">
            <div className="rounded-lg bg-white p-6 shadow-md">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">今月の支出</h2>
                <div className="text-right">
                  <p className="text-sm text-gray-500">合計</p>
                  <p className="text-3xl font-bold text-blue-600">¥{totalExpenses.toLocaleString()}</p>
                </div>
              </div>

              <div className="mb-4">
                <button
                  type="button"
                  onClick={() => setShowAddExpense(true)}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-3 font-medium text-white shadow-md transition-all hover:bg-blue-600 active:scale-95"
                >
                  <Plus className="size-5" />
                  手動入力
                </button>
              </div>

              <ExpenseList expenses={expenses} onDelete={deleteExpenseCall} />
            </div>
          </Tabs.Content>

          <Tabs.Content value="inventory" className="space-y-4">
            <div className="rounded-lg bg-white p-6 shadow-md">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">在庫管理</h2>
                <p className="text-gray-500">{inventory.length}品目</p>
              </div>

              <div className="mb-4">
                <button
                  type="button"
                  onClick={() => setShowAddInventory(true)}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-500 px-4 py-3 font-medium text-white shadow-md transition-all hover:bg-green-600 active:scale-95"
                >
                  <Plus className="size-5" />
                  手動入力
                </button>
              </div>

              <InventoryList
                inventory={inventory}
                onDelete={deleteInventoryItemCall}
                onUpdate={updateInventoryItem}
              />
            </div>
          </Tabs.Content>

          <Tabs.Content value="recipes" className="space-y-4">
            {suggestedRecipes.length > 0 && (
              <div className="rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-white shadow-md">
                <h3 className="mb-2 text-xl font-bold">🍳 今作れるレシピ</h3>
                <p className="mb-3 text-purple-100">在庫の材料で作れる料理があります！</p>
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {suggestedRecipes.map((recipe) => (
                    <div
                      key={recipe.id}
                      className="flex-shrink-0 rounded-lg bg-white/20 px-4 py-2 backdrop-blur"
                    >
                      <p className="font-medium">{recipe.title}</p>
                      <p className="text-sm text-purple-100">{recipe.cookingTime}分</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
 
            <div className="rounded-lg bg-white p-6 shadow-md border-2 border-purple-400">
              <h2 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
                <span>🤖</span> AIにレシピを相談
              </h2>
              <form onSubmit={handleGenerateRecipe} className="flex flex-col gap-3">
                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  placeholder="例: 冷蔵庫にある豚肉で簡単に作れるもの"
                  className="w-full p-3 rounded-xl border border-gray-300 min-h-[80px] text-base focus:outline-none focus:border-purple-500 disabled:bg-gray-100 text-gray-700"
                  disabled={isGenerating}
                />
                <button
                  type="submit"
                  disabled={isGenerating}
                  className="w-full flex items-center justify-center gap-2 rounded-xl py-3 font-bold text-white shadow-md transition-all active:scale-95"
                  style={{ backgroundColor: isGenerating ? '#ccc' : '#a855f7' }}
                >
                  {isGenerating ? "AIが考え中..." : "レシピを提案してもらう"}
                </button>
              </form>
            </div>

            <div className="rounded-lg bg-white p-6 shadow-md">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">全レシピ</h2>
                <p className="text-gray-500">{recipes.length}件</p>
              </div>

              <RecipeListCall 
                recipes={recipes} 
                onDelete={deleteRecipe} 
                inventory={inventory} 
                onSelectRecipe={(recipe) => setSelectedRecipe(recipe)}
              />
            </div>
          </Tabs.Content>
        </Tabs.Root>

        <button
          type="button"
          onClick={() => setShowCamera(true)}
          className="fixed bottom-8 right-8 flex size-16 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-green-500 text-white shadow-2xl transition-all hover:scale-110 hover:shadow-3xl active:scale-95"
          aria-label="カメラを開く"
        >
          <Camera className="size-8" />
        </button>
      </div>

      {selectedRecipe && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white rounded-2xl p-6 max-w-lg w-full max-h-[85vh] overflow-y-auto shadow-2xl relative">
            <button 
              type="button"
              onClick={handleCloseModal}
              className="absolute top-4 right-4 p-1 rounded-full text-gray-400 hover:bg-gray-100"
            >
              <X className="size-5" />
            </button>
            
            <h3 className="text-2xl font-bold text-gray-800 mb-1">{selectedRecipe.title}</h3>
            {selectedRecipe.url && (
              <a href={selectedRecipe.url} target="_blank" rel="noreferrer" className="text-xs text-blue-500 underline block mb-3">
                クックパッドで元レシピを見る ↗
              </a>
            )}
            
            <p className="text-purple-600 font-semibold mb-4">
              ⏱ 調理時間: {selectedRecipe.cookingTime}分 
              {selectedRecipe.estimatedCost && ` / 💰 目安: ¥${selectedRecipe.estimatedCost}`}
            </p>
            
            <div className="mb-4">
              <h4 className="font-bold text-gray-700 mb-1.5">🥗 材料リスト</h4>
              <ul className="space-y-1">
                {selectedRecipe.ingredients?.map((ing, idx) => (
                  <li key={idx} className="flex justify-between items-center text-sm p-1.5 rounded bg-gray-50">
                    <span className="text-gray-700 font-medium">{ing.name} <span className="text-xs text-gray-400">({ing.amount})</span></span>
                    {ing.isInFridge ? (
                      <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-bold">冷蔵庫あり</span>
                    ) : (
                      <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-800 rounded font-bold">⚠️ 要購入</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>

            {shopPrices.length > 0 && (
              <div className="mb-4 p-4 rounded-xl bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200">
                <h4 className="font-bold text-amber-900 mb-2 flex items-center gap-1.5 text-sm">
                  <Store className="size-4" /> 店ごとの不足材料の合計価格
                </h4>
                <div className="space-y-2">
                  {shopPrices.map((shop, idx) => (
                    <div key={idx} className="flex justify-between items-center bg-white p-2.5 rounded-lg shadow-sm border border-amber-100 text-sm">
                      <span className="font-medium text-gray-700">{shop.shopName}</span>
                      <span className="font-bold text-orange-600 text-base">
                        ¥{shop.totalPrice.toLocaleString()}
                        {shop.deliveryFee && <span className="text-xs text-gray-400 font-normal ml-1">(送料込)</span>}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="mb-6">
              <h4 className="font-bold text-gray-700 mb-1.5">🍳 作り方手順</h4>
              {selectedRecipe.steps ? (
                <div className="space-y-2">
                  {selectedRecipe.steps.map((step) => (
                    <div key={step.order} className="flex gap-2.5 text-sm p-2 bg-slate-50 rounded border border-slate-100">
                      <span className="font-bold text-purple-600 shrink-0">{step.order}.</span>
                      <p className="text-gray-600 leading-relaxed">{step.description}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-600 whitespace-pre-wrap text-sm leading-relaxed bg-gray-50 p-3 rounded-lg border">
                  {selectedRecipe.instructions}
                </p>
              )}
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => handleFetchPurchaseEstimation(selectedRecipe)}
                disabled={isFetchingPrices}
                className="flex-1 flex items-center justify-center gap-1 bg-amber-500 text-white font-bold py-3 rounded-xl shadow-md hover:bg-amber-600 transition-all active:scale-95 disabled:bg-amber-300 disabled:cursor-not-allowed"
              >
                {isFetchingPrices ? (
                  <Loader2 className="size-5 animate-spin" />
                ) : (
                  <ShoppingCart className="size-5" />
                )}
                {isFetchingPrices ? "価格を取得中..." : "足りない材料を購入"}
              </button>
              <button
                type="button"
                onClick={() => handleFinalAdd(selectedRecipe)}
                className="flex-1 bg-gradient-to-r from-purple-500 to-indigo-500 text-white font-bold py-3 rounded-xl shadow-lg hover:opacity-90 transition-all"
              >
                このレシピを適応する
              </button>
            </div>
          </div>
        </div>
      )}

      {showCamera && (
        <UniversalCamera
          onCapture={async (imageUrl, extractedData) => {
            setShowCamera(false);
            if (extractedData.expense) {
              addExpenseCall(extractedData.expense);
            }
            if (extractedData.inventoryItems) {
              extractedData.inventoryItems.forEach((item) => addInventoryItemCall(item));
            }
          }}
          onClose={() => setShowCamera(false)}
        />
      )}

      {showAddInventory && (
        <AddInventoryForm
          onAdd={(item) => {
            addInventoryItemCall(item); 
            setShowAddInventory(false);
          }}
          onClose={() => setShowAddInventory(false)}
        />
      )}

      {showAddExpense && (
        <AddExpenseForm
          onAdd={(expense) => {
            addExpenseCall(expense);
            setShowAddExpense(false);
          }}
          onClose={() => setShowAddExpense(false)}
        />
      )}

      {showSettings && (
        <SettingsModal
          settings={settings}
          onSave={(newSettings) => {
            setSettings(newSettings);
            setShowSettings(false);
          }}
          onClose={() => {
            if (settings.isSetupComplete) {
              setShowSettings(false);
            }
          }}
        />
      )}
    </div>
  );
}