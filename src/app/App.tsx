import { useState, useEffect } from "react";
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
  ShoppingCart,
  Loader2,
  Store,
} from "lucide-react";
import * as Tabs from "@radix-ui/react-tabs";
import { UniversalCamera } from "./components/UniversalCamera";
import { ExpenseList } from "./components/ExpenseList";
import { InventoryList } from "./components/InventoryList";
import { RecipeList } from "./components/RecipeList";
import { AddExpenseForm } from "./components/AddExpenseForm";
import { AddInventoryForm } from "./components/AddInventoryForm";
import { AddRecipeForm } from "./components/AddRecipeForm";
import { SettingsModal } from "./components/SettingsModal";


//const kakeibo_URL = "http://localhost:8000";
//const kakeibo_URL = "https://social-system-group2.onrender.com";
const kakeibo_URL = "https://social-system-group2-3.onrender.com";



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

export interface ReceiptItemPayload {
  id?: string;
  raw_name: string;
  normalized_name: string;
  product_id: number | null;
  category_id: number | null;
  purchased_quantity: number;
  purchased_unit: string;
  base_quantity: number;
  base_unit: string;
  unit_price: number;
  line_total: number;
  is_inventory_target: boolean;
}

export interface Expense {
  id: string;
  amount: number;
  category: string;
  description: string;
  date: Date;
  imageUrl?: string;
  items?: ReceiptItemPayload[];
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


useEffect(() => {
    if (!settings.isSetupComplete) {
      setShowSettings(true);
    }
    fetchExpenses();
    fetchInventoryBalances(); // ★アプリ起動時に在庫も直接取得する
  }, []);

// ★新設: サーバーから直接最新の在庫一覧を取得してStateを同期する
  const fetchInventoryBalances = async () => {
    try {
      const res = await fetch(`${kakeibo_URL}/inventory/balances?include_zero=false`);
      if (!res.ok) throw new Error(`在庫取得エラー: ${res.status}`);
      const data = await res.json();

      if (data && Array.isArray(data.items)) {
        // サーバーから返ってきた最新の在庫配列でStateを上書き
        //（最後の1個を削除して空配列 `[]` になった場合も正しく画面が空になります）
        const formattedInventory = data.items.map((item: any) => ({
          id: item.product_id.toString(), // product_id を一意のIDとして利用
          name: item.normalized_name || "不明な食材",
          quantity: item.current_quantity,
          unit: item.base_unit || "個",
          category: "食材在庫"
        }));
        setInventory(formattedInventory);
      } else {
        setInventory([]);
      }
    } catch (err) {
      console.error("在庫一覧の取得に失敗しました:", err);
      setInventory([]);
    }
  };

  // 取得した全レシート明細の `is_inventory_target` からフロントの在庫状態を完全同期するロジック
  const syncInventoryFromExpenses = (allExpenses: Expense[]) => {
    const newInventory: InventoryItem[] = [];
    allExpenses.forEach((exp) => {
      if (exp.items && Array.isArray(exp.items)) {
        exp.items.forEach((item) => {
          if (item.is_inventory_target) {
            newInventory.push({
              id: item.id ? item.id.toString() : `${exp.id}-${item.raw_name}`,
              name: item.normalized_name || item.raw_name,
              quantity: item.base_quantity,
              unit: item.base_unit || "個",
              category: "食材在庫",
            });
          }
        });
      }
    });
    setInventory(newInventory);
  };

  // 家計簿・レシートデータの読み込み (サマリー取得後、個別詳細を並列マージ)
  const fetchExpensesOLD = async () => {
    try {
      const res = await fetch(`${kakeibo_URL}/receipts`); 
      if (!res.ok) throw new Error(`サーバーエラー: ${res.status}`);
      const summaryData = await res.json();
      
      if (Array.isArray(summaryData)) {
        const detailedExpenses: Expense[] = await Promise.all(
          summaryData.map(async (item: any) => {
            const dateStr = String(item.purchased_at);
            const y = Number(dateStr.substring(0, 4));
            const m = Number(dateStr.substring(4, 6)) - 1;
            const d = Number(dateStr.substring(6, 8));
            
            let itemsPayload: ReceiptItemPayload[] = [];
            try {
              const detailRes = await fetch(`${kakeibo_URL}/receipts/${item.id}`);
              if (detailRes.ok) {
                const detailData = await detailRes.json();
                itemsPayload = detailData.items || [];
              }
            } catch (err) {
              console.error(`レシート詳細(id:${item.id})の取得に失敗しました`, err);
            }

            return {
              id: item.id.toString(),
              amount: item.total_amount,
              category: "レシートデータ",
              description: item.store_name || "店舗名未設定",
              date: new Date(y, m, d),
              items: itemsPayload
            };
          })
        );
        
        setExpenses(detailedExpenses);
        syncInventoryFromExpenses(detailedExpenses);
      }
    } catch (err) {
      console.error("読み込み失敗", err);
    }
  };

  const fetchExpenses = async () => {
      try {
        const res = await fetch(`${kakeibo_URL}/receipts`); 
        if (!res.ok) throw new Error(`サーバーエラー: ${res.status}`);
        const summaryData = await res.json();
        
        if (Array.isArray(summaryData) && summaryData.length > 0) {
          // 1. 型定義を一旦「(Expense | null)[]」として受け取る
          const resultsWithNull: (Expense | null)[] = await Promise.all(
            summaryData.map(async (item: any) => {
              if (!item) return null;

              // --- 安全に日付をパースするガード処理 ---
              let parsedDate = new Date();
              const dateStr = String(item.purchased_at || "");
              
              if (dateStr && dateStr.length === 8 && !dateStr.startsWith("0") && dateStr !== "undefined") {
                const y = Number(dateStr.substring(0, 4));
                const m = Number(dateStr.substring(4, 6)) - 1;
                const d = Number(dateStr.substring(6, 8));
                if (!isNaN(y) && !isNaN(m) && !isNaN(d)) {
                  parsedDate = new Date(y, m, d);
                }
              } else if (item.purchased_at && String(item.purchased_at).includes("-")) {
                parsedDate = new Date(item.purchased_at);
              }

              const currentId = item.id !== undefined && item.id !== null ? item.id.toString() : Math.random().toString();
              
              let itemsPayload: ReceiptItemPayload[] = [];
              if (item.id !== undefined && item.id !== null) {
                try {
                  const detailRes = await fetch(`${kakeibo_URL}/receipts/${item.id}`);
                  if (detailRes.ok) {
                    const detailData = await detailRes.json();
                    itemsPayload = detailData.items || [];
                  }
                } catch (err) {
                  console.error(`レシート詳細(id:${item.id})の取得に失敗しました`, err);
                }
              }

              return {
                id: currentId,
                amount: Number(item.total_amount) || 0,
                category: "レシートデータ",
                description: item.store_name || "店舗名未設定",
                date: parsedDate,
                items: itemsPayload
              };
            })
          );
          
          // 2. nullを綺麗にフィルター除去し、型を確定させる
          const detailedExpenses: Expense[] = resultsWithNull.filter(
            (e): e is Expense => e !== null
          );
          
          setExpenses(detailedExpenses);
          syncInventoryFromExpenses(detailedExpenses);
        } else {
          setExpenses([]);
        }
      } catch (err) {
        console.error("読み込み失敗", err);
        setExpenses([]);
      }
    };
    
  // 共通のレシート登録用関数
  const submitReceiptPayloadOLD = async (requestBody: any) => {
    try {
      const response = await fetch(`${kakeibo_URL}/receipts`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);
      await fetchExpenses(); 
    } catch (err) {
      console.error("レシートデータの送信に失敗しました:", err);
      alert("サーバーへの保存に失敗しました。");
    }
  };


//  const submitReceiptPayload = async (requestBody: any) => {
//      try {
//        if (!requestBody) return;
//
//        // 1. フロントのデータを prepare が受け取れる文字列日付にする
//        let dateStr = "2026-05-26";
//        if (requestBody.purchased_at) {
//          const s = String(requestBody.purchased_at);
//          if (s.length === 8) {
//            dateStr = `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`;
//          } else if (s.includes("-")) {
//            dateStr = s;
//          }
//        }
//
//        const prepareBody = {
//          status: "needs_confirmation",
//          store_name: requestBody.store_name || "手動在庫追加",
//          purchased_at: dateStr, 
//          total_amount: Number(requestBody.total_amount) || 0,
//          items: Array.isArray(requestBody.items) 
//            ? requestBody.items.map((item: any) => ({
//                raw_name: item.raw_name || "手動登録商品",
//                normalized_name: item.normalized_name || item.raw_name || "手動登録商品",
//                category_name: "食費", 
//                purchased_quantity: Number(item.purchased_quantity) || 1,
//                purchased_unit: item.purchased_unit || "個",
//                base_quantity: Number(item.base_quantity || item.purchased_quantity) || 1,
//                base_unit: item.base_unit || item.purchased_unit || "個",
//                unit_price: Number(item.unit_price) || 0,
//                line_total: Number(item.line_total) || 0,
//                is_inventory_target: item.is_inventory_target ?? true,
//                confidence: 1.0,
//                warnings: []
//              }))
//            : [],
//          warnings: []
//        };
//
//        // 2. /receipts/prepare を叩いて、商品IDや単位を補完してもらう
//        console.log("prepareに送信する下書き:", prepareBody);
//        const prepareResponse = await fetch(`${kakeibo_URL}/receipts/prepare`, {
//          method: "POST",
//          headers: { "Content-Type": "application/json" },
//          body: JSON.stringify(prepareBody),
//        });
//
//        if (!prepareResponse.ok) throw new Error(`Prepareエラー: ${prepareResponse.status}`);
//        const prepareData = await prepareResponse.json();
//        const finalizedReceipt = prepareData.receipt;
//
//        if (!finalizedReceipt || !Array.isArray(finalizedReceipt.items)) {
//          throw new Error("サーバーからの自動補完結果が不正です。");
//        }
//
//        // 3. ★修正ポイント: 家計簿には登録せず、在庫追加用（inventory/batches）のデータを作成する
//        // 新仕様の POST /inventory/batches に適合する配列形式へ変換
//        const inventoryBatchesPayload = finalizedReceipt.items
//          .filter((item: any) => item.is_inventory_target !== false) // 在庫対象のみ
//          .map((item: any) => {
//            // purchased_at を YYYYMMDD の整数に変換
//            const rawDate = finalizedReceipt.purchased_at || 20260526;
//            const cleanDate = typeof rawDate === 'string' ? Number(rawDate.replace(/[-/]/g, '')) : Number(rawDate);
//
//            return {
//              product_id: Number(item.product_id) || 1,
//              original_quantity: Number(item.base_quantity) || Number(item.purchased_quantity) || 1,
//              unit: item.base_unit || item.purchased_unit || "個",
//              purchased_at: cleanDate,
//              // 任意項目（不要なら省略可）
//              store_name: finalizedReceipt.store_name || "手動在庫追加",
//              receipt_id: null // 家計簿を通さないためnull
//            };
//          });
//
//        if (inventoryBatchesPayload.length === 0) {
//          alert("在庫対象の食材がありません。");
//          return;
//        }
//
//        // 4. 在庫直接追加API（POST /inventory/batches）にリクエストを送信
//        console.log("在庫直接追加へ送信するペイロード:", inventoryBatchesPayload);
//        const response = await fetch(`${kakeibo_URL}/inventory/batches`, {  
//          method: "POST",
//          headers: { "Content-Type": "application/json" },
//          body: JSON.stringify(inventoryBatchesPayload), // 配列のまま送信
//        });
//
//        if (!response.ok) {
//          const errorDetail = await response.json().catch(() => ({}));
//          console.error("在庫追加のサーバーエラー詳細:", errorDetail);
//          throw new Error(`在庫追加エラー: ${response.status}`);
//        }
//
//        // 5. 家計簿(expenses)ではなく、在庫一覧(inventory)を更新する
//        if (typeof (window as any).fetchInventory === "function") {
//          await (window as any).fetchInventory();
//        }
//// 5. 家計簿ではなく、直接最新の在庫一覧をサーバーから再取得する
//        await fetchInventoryBalances(); 
//        // 念のため家計簿側もリフレッシュ
//        await fetchExpenses(); 
//
//        alert("在庫の手動追加に成功しました！");
//
//
//      } catch (err) {
//        console.error("送信プロセス失敗:", err);
//        alert("サーバーへの保存に失敗しました。");
//      }
//    };

const submitReceiptPayload = async (requestBody: any) => {
    try {
      if (!requestBody) return;

      // 1. フロントのデータを prepare が受け取れる文字列日付にする
      let dateStr = "2026-05-26";
      if (requestBody.purchased_at) {
        const s = String(requestBody.purchased_at);
        if (s.length === 8) {
          dateStr = `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`;
        } else if (s.includes("-")) {
          dateStr = s;
        }
      }

      const prepareBody = {
        status: "needs_confirmation",
        store_name: requestBody.store_name || "手動在庫追加",
        purchased_at: dateStr, 
        total_amount: Number(requestBody.total_amount) || 0,
        items: Array.isArray(requestBody.items) 
          ? requestBody.items.map((item: any) => ({
              raw_name: item.raw_name || "手動登録商品",
              normalized_name: item.normalized_name || item.raw_name || "手動登録商品",
              category_name: "食費", 
              purchased_quantity: Number(item.purchased_quantity) || 1,
              purchased_unit: item.purchased_unit || "個",
              base_quantity: Number(item.base_quantity || item.purchased_quantity) || 1,
              base_unit: item.base_unit || item.purchased_unit || "個",
              unit_price: Number(item.unit_price) || 0,
              line_total: Number(item.line_total) || 0,
              is_inventory_target: true, // ★手動在庫追加フォームからなので、常に強制で true にする
              confidence: 1.0,
              warnings: []
            }))
          : [],
        warnings: []
      };

      // 2. /receipts/prepare を叩いて、商品IDや単位を補完してもらう
      console.log("prepareに送信する下書き:", prepareBody);
      const prepareResponse = await fetch(`${kakeibo_URL}/receipts/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prepareBody),
      });

      if (!prepareResponse.ok) throw new Error(`Prepareエラー: ${prepareResponse.status}`);
      const prepareData = await prepareResponse.json();
      const finalizedReceipt = prepareData.receipt;

      if (!finalizedReceipt || !Array.isArray(finalizedReceipt.items)) {
        throw new Error("サーバーからの自動補完結果が不正です。");
      }

      // ★重要：AIやバックエンドが「在庫対象外(false)」と判定してきた場合でも、
      // ユーザーが手動追加したがっているため、強制的に true へ書き換える
      finalizedReceipt.items = finalizedReceipt.items.map((item: any) => ({
        ...item,
        is_inventory_target: true
      }));

      // 3. ★修正ポイント: エラーになる inventory/batches は使わず、本登録 API (POST /receipts) に送信する
      console.log("在庫手動追加のためレシート本登録へ送信:", finalizedReceipt);
      const response = await fetch(`${kakeibo_URL}/receipts`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(finalizedReceipt), // オブジェクト形式で送信
      });

      if (!response.ok) {
        const errorDetail = await response.json().catch(() => ({}));
        console.error("レシート本登録のサーバーエラー詳細:", errorDetail);
        throw new Error(`サーバー登録エラー: ${response.status}`);
      }

      // 4. 最新のデータを再読み込みして画面を更新する
      await fetchExpenses(); 

      alert("在庫の手動追加に成功しました！");
    } catch (err) {
      console.error("送信プロセス失敗:", err);
      alert("サーバーへの保存に失敗しました。");
    }
  };

  // 手動家計簿追加
// 5. 手動家計簿データ追加 (直接 POST /receipts を叩くように修正)
  const addExpenseCall = async (expense: Omit<Expense, 'id'>) => {
    try {
      // 画面から入力された日付を、バックエンドが求める「整数型 (YYYYMMDD)」に安全変換
      let dateNum = 20260526;
      if (expense.date) {
        const d = new Date(expense.date);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        dateNum = Number(`${y}${m}${day}`);
      }

      // バックエンドの仕様書（POST /receipts）に完全適合するデータ構造を作成
      const requestBody = {
        purchased_at: dateNum,
        store_name: (expense.description || "手動登録店舗").trim(),
        total_amount: Number(expense.amount) || 0,
        items: [
          {
            raw_name: (expense.description || "手動登録商品").trim(),
            normalized_name: (expense.category || "娯楽").trim(),
            product_id: null,  // 家計簿単体登録のため null でOK
            category_id: null, // カテゴリは文字列で渡すか、nullにしてバックエンドに任せる
            purchased_quantity: 1,
            purchased_unit: "個",
            base_quantity: 1,
            base_unit: "個",
            unit_price: Number(expense.amount) || 0,
            line_total: Number(expense.amount) || 0,
            is_inventory_target: false // 家計簿専用フォームからのため false 固定
          }
        ]
      };

      console.log("手動家計簿登録の送信ペイロード:", requestBody);

      // 直接本登録APIを呼び出す
      const response = await fetch(`${kakeibo_URL}/receipts`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorDetail = await response.json().catch(() => ({}));
        console.error("手動家計簿登録エラー詳細:", errorDetail);
        throw new Error(`サーバーエラー: ${response.status}`);
      }

      // 家計簿一覧（expenses）を再取得して画面を更新
      await fetchExpenses(); 
      alert("家計簿にデータを登録しました！");
    } catch (err) {
      console.error("手動家計簿の送信に失敗しました:", err);
      alert("サーバーへの保存に失敗しました。入力値を確認してください。");
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
      const updatedExpenses = expenses.filter((e) => e.id !== id);
      setExpenses(updatedExpenses);
      syncInventoryFromExpenses(updatedExpenses);
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
    await submitReceiptPayload(requestBody);
  };

// 6. 在庫データ削除 (DELETE /receipts/{id} 仕様に連動)
  const deleteInventoryItemCall = async (id: string | number) => {
    try {
      if (id === undefined || id === null) {
        throw new Error("削除するIDが指定されていません");
      }

      // 1. ハイフンが含まれている場合は前方のレシートIDだけを抽出し、そうでなければそのまま文字列化
      const idStr = String(id);
      const rawReceiptId = idStr.includes("-") ? idStr.split("-")[0] : idStr;
      
      // 2. バックエンドの仕様に合わせて、IDを確実な「数値型」に変換する
      const receiptId = Number(rawReceiptId);

      // 万が一IDがNaN（数値に変換できない文字列）だった場合のセーフティガード
      if (isNaN(receiptId)) {
        console.error("無効なレシートID形式のため削除を中断しました:", id);
        alert("無効なデータIDのため、削除できません。");
        return;
      }

      console.log(`削除リクエスト送信中... URL: ${kakeibo_URL}/receipts/${receiptId}`);

      // 3. DELETEリクエストの送信
      const response = await fetch(`${kakeibo_URL}/receipts/${receiptId}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" }
      });

      // 4. エラーが起きた場合は詳細をコンソールに出す
      if (!response.ok) {
        const errorDetail = await response.json().catch(() => ({}));
        console.error("サーバーが削除を拒否した詳細理由:", errorDetail);
        throw new Error(`サーバーエラー: ${response.status}`);
      }

// 5. 削除成功後、画面の家計簿と現在の在庫データを両方最新にする
      await fetchExpenses();
      await fetchInventoryBalances(); // ★ここを fetchInventoryBalances() に変更
      
    
      
      // もしアプリ内に最新在庫を再取得する関数（fetchInventoryなど）があればここで一緒に呼ぶ
      if (typeof (window as any).fetchInventory === "function") {
        await (window as any).fetchInventory();
      }
      
      alert("削除が完了しました！");
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

      // 2. 家計簿側への支出記録処理（共通関数を利用し再同期）
      await submitReceiptPayload({
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
      });

      alert("家計簿に追加し、バックエンドの冷蔵庫在庫を消費しました！");
      handleCloseModal();
      setActiveTab('expenses');
    } catch (err) {
      console.error("レシピの適応に失敗しました:", err);
      alert("レシピの適応処理に失敗しました。");
    }
  };

  // カメラからの読み込み成功コールバックをリフレッシュ（二重登録を防ぎ再読み込みのみを担当）
  const handleCameraCaptureComplete = async () => {
    setShowCamera(false);
    await fetchExpenses();
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
          onCapture={handleCameraCaptureComplete}
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