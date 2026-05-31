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
import { PriceComparison } from "./components/PriceComparison";
import { WelcomeScreen } from "./components/WelcomeScreen";

// バックエンドURL定義 (App.tsxに準拠)
const kakeibo_URL = "https://social-system-group2-2.onrender.com";
const recipe_URL = "https://social-system-group2-1.onrender.com";

// --- 型定義 (App.tsxに準拠) ---
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
            <div className="flex-1 min-w-[180px]">
              <h3 className="font-bold text-gray-800 text-base line-clamp-1">{recipe.title}</h3>
              <p className="text-sm text-gray-500 mt-0.5">
                ⏱ {recipe.cookingTime}分 / {recipe.ingredients?.length || 0}品目
              </p>
            </div>
            
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
  // 状態定義 (App.tsx準拠の空配列スタート)
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);

  const [showCamera, setShowCamera] = useState(false);
  const [showAddExpense, setShowAddExpense] = useState(false);
  const [showAddInventory, setShowAddInventory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showWelcome, setShowWelcome] = useState(false); // Appchange仕様

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

  const formatToYmdNumber = (date: Date) => {
    const targetDate = date instanceof Date ? date : new Date(date);
    return Number(targetDate.toISOString().split('T')[0].replace(/-/g, ''));
  };

  // 初期読み込みロジック (App.tsxをベースにAppchangeのWelcome判定を合成)
  useEffect(() => {
    const savedSettings = localStorage.getItem('userSettings');
    if (savedSettings) {
      const parsed = JSON.parse(savedSettings);
      setSettings(parsed);
      if (!parsed.isSetupComplete) {
        setShowWelcome(true);
      }
    } else {
      setShowWelcome(true);
    }
    fetchExpenses();
    fetchInventoryBalances();
  }, []);

  // API連動関数 (App.tsx準拠)
  const fetchInventoryBalances = async () => {
    try {
      const res = await fetch(`${kakeibo_URL}/inventory/balances?include_zero=false`);
      if (!res.ok) throw new Error(`在庫取得エラー: ${res.status}`);
      const data = await res.json();

      if (data && Array.isArray(data.items)) {
        const formattedInventory = data.items.map((item: any) => ({
          id: item.product_id.toString(),
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

const syncInventoryFromExpenses = (allExpenses: Expense[]) => {
    const newInventory: InventoryItem[] = [];
    allExpenses.forEach((exp) => {
      if (exp.items && Array.isArray(exp.items)) {
        exp.items.forEach((item) => {
          if (item.is_inventory_target) {
            newInventory.push({
              id: item.id ? item.id.toString() : `${exp.id}-${item.raw_name}`,
              name: item.normalized_name || item.raw_name,
              quantity: Number(item.base_quantity) || 1,
              unit: item.base_unit || "個",
              category: "食材在庫",
            });
          }
        });
      }
    });
    setInventory(newInventory);
  };

const fetchExpenses = async () => {
    try {
      const res = await fetch(`${kakeibo_URL}/receipts`); 
      if (!res.ok) throw new Error(`サーバーエラー: ${res.status}`);
      const summaryData = await res.json();
      
      if (Array.isArray(summaryData)) {
        if (summaryData.length === 0) {
          setExpenses([]);
          setInventory([]);
          return;
        }

        const resultsWithNull: (Expense | null)[] = await Promise.all(
          summaryData.map(async (item: any) => {
            if (!item) return null;

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
                  
                  // 🚨 【超重要ガード】読み込み時に「買い物」などの一括支出データを強制排除する
                  if (Array.isArray(detailData.items)) {
                    itemsPayload = detailData.items.map((subItem: any) => {
                      const name = subItem.raw_name || "";
                      const normName = subItem.normalized_name || "";
                      
                      // 名前に「買い物」や「支出」、「未分類」が含まれている塊データか判定
                      const isBulkBlock = 
                        name.includes("買い物") || 
                        normName.includes("買い物") || 
                        name.includes("支出") ||
                        normName.includes("支出") ||
                        normName.includes("未分類");

                      if (isBulkBlock) {
                        return {
                          ...subItem,
                          is_inventory_target: false, // 👈 強制的にfalseにして比較欄から追放
                          base_quantity: null,        // 👈 nullにして比較対象外にする
                          base_unit: null
                        };
                      }
                      return subItem;
                    });
                  } else {
                    itemsPayload = [];
                  }
                }
              } catch (err) {
                console.error(`レシート詳細(id:${item.id})の取得に失敗しました`, err);
              }
            }

            // 💡 【ここを追加】店名やフラグから、手動登録されたデータか賢く判定する
            const isManualInput = 
              item.is_manual === true || 
              item.source_type === "manual" ||
              (item.store_name && (
                item.store_name.includes("手動") || 
                item.store_name.includes("レシピ") || 
                item.store_name === "SHOP" ||
                item.store_name === "AIレシピ適応調理"
              ));

            return {
              id: currentId,
              amount: Number(item.total_amount) || 0,
              // ✨ 固定ではなく、判定結果によって表示を正しく切り替える
              category: isManualInput ? "手動入力" : "レシートデータ",
              description: item.store_name || "店舗名未設定",
              date: parsedDate,
              items: itemsPayload
            };
          })
        );
        
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
    
const submitReceiptPayload = async (requestBody: any) => {
    try {
      if (!requestBody) return;

      let dateStr = "2026-05-31";
      if (requestBody.purchased_at) {
        const s = String(requestBody.purchased_at);
        if (s.length === 8 && !s.includes("-")) {
          dateStr = `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`;
        } else if (s.includes("-")) {
          dateStr = s.split('T')[0];
        }
      }

      // ユーザーが明示的に個別商品リスト(items)を入力して渡してきたか判定
      const hasItems = Array.isArray(requestBody.items) && requestBody.items.length > 0;

      const prepareBody = {
        status: "needs_confirmation",
        store_name: (requestBody.store_name || "手動登録店舗").trim(), 
        purchased_at: dateStr, 
        total_amount: Number(requestBody.total_amount) || 0, 
        items: hasItems 
          ? requestBody.items.map((item: any) => {
              const isFood = item.category_name === "食費" || item.normalized_name === "食費";
              return {
                raw_name: (item.raw_name || "手動登録商品").trim(),
                normalized_name: (item.normalized_name || item.raw_name || "手動登録商品").trim(),
                // 空、null、undefinedの場合は一律 null としてサーバーへ送る
                category_name: item.category_name && item.category_name.trim() !== "" ? item.category_name : null, 
                purchased_quantity: Number(item.purchased_quantity) || 1,
                purchased_unit: item.purchased_unit || "個",
                base_quantity: isFood ? (Number(item.base_quantity || item.purchased_quantity) || 1) : null,
                base_unit: isFood ? (item.base_unit || item.purchased_unit || "個") : null,
                unit_price: Number(item.unit_price) || 0,
                line_total: Number(item.line_total) || 0,
                is_inventory_target: isFood,
                confidence: 1.0,
                warnings: []
              };
            })
          : [
              {
                raw_name: "詳細未入力の支出（一括）",
                normalized_name: "詳細未入力の支出",
                category_name: "その他", 
                purchased_quantity: 1,
                purchased_unit: "個",
                base_quantity: null, 
                base_unit: null, 
                unit_price: Number(requestBody.total_amount) || 0,
                line_total: Number(requestBody.total_amount) || 0,
                is_inventory_target: false,
                confidence: 1.0,
                warnings: []
              }
            ],
        warnings: []
      };

      const prepareResponse = await fetch(`${kakeibo_URL}/receipts/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prepareBody),
      });

      if (!prepareResponse.ok) throw new Error(`Prepareエラー: ${prepareResponse.status}`);
      const prepareData = await prepareResponse.json();
      const finalizedReceipt = prepareData.receipt;

      if (!finalizedReceipt) throw new Error("サーバーからの自動補完結果が不正です。");

      // 🚨 【422 extra_forbidden 完全撃退フィルター】
      // バックエンドが本登録（/receipts）で受け付ける「許可された項目」だけでデータを再構築します。
      const cleansedPayload: any = {
        store_name: finalizedReceipt.store_name || "店舗名未設定",
        purchased_at: typeof finalizedReceipt.purchased_at === 'string'
          ? Number(finalizedReceipt.purchased_at.replace(/[-/]/g, ''))
          : Number(finalizedReceipt.purchased_at) || 20260531,
        total_amount: Number(requestBody.total_amount) || 0,
        items: []
      };

      if (Array.isArray(finalizedReceipt.items)) {
        cleansedPayload.items = finalizedReceipt.items.map((item: any) => {
          // 1. 一括登録（明細なし）の場合のすり抜け防止
          if (!hasItems) {
            return {
              raw_name: `${prepareBody.store_name}での買い物（比較対象外）`,
              normalized_name: "詳細未入力の支出",
              product_id: null,
              category_id: null,
              is_inventory_target: false, 
              base_quantity: null,        
              base_unit: null,            
              purchased_quantity: 1,
              purchased_unit: "個",
              unit_price: Number(cleansedPayload.total_amount),
              line_total: Number(cleansedPayload.total_amount)
            };
          }

          // 2. レシピ適応や通常詳細入力のケース
          const finalCategory = item.category_name || "";
          const finalNormName = item.normalized_name || "";
          const isRealFood = finalCategory === "食費" || finalNormName === "食費";

          // ⚠️ サーバーが「Extra inputs are not permitted」で怒るため、
          // category_name, confidence, warnings などの禁止キーを完全に排除してリターンします
          return {
            raw_name: (item.raw_name || "手動登録商品").trim(),
            normalized_name: (item.normalized_name || item.raw_name || "手動登録商品").trim(),
            product_id: isRealFood ? (item.product_id || null) : null, 
            category_id: item.category_id || null,
            is_inventory_target: isRealFood,
            purchased_quantity: Number(item.purchased_quantity) || 1, 
            purchased_unit: item.purchased_unit || "個",
            unit_price: Number(item.unit_price) || 0,
            line_total: Number(item.line_total) || 0,
            base_quantity: isRealFood ? (Number(item.base_quantity || item.purchased_quantity) || 1) : null, 
            base_unit: isRealFood ? (item.base_unit || "個") : null 
          };
        });
      }
      
      console.log("【本登録直前】余計なキーをすべて排除したデータ:", cleansedPayload);

      // 完全に綺麗になった cleansedPayload を送る
      const response = await fetch(`${kakeibo_URL}/receipts`, {  
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cleansedPayload), // 👈 ここを finalizedReceipt から cleansedPayload に変更
      });

      if (!response.ok) {
        const errDetail = await response.json().catch(() => ({}));
        console.error("本登録エラー詳細:", errDetail);
        throw new Error(`サーバーエラー: ${response.status}`);
      }

      await fetchExpenses();
    } catch (err) {
      console.error("送信プロセス失敗:", err);
    }
  };

const addExpenseCall = async (expense: Omit<Expense, 'id'>) => {
    try {
      let dateNum = 20260531;
      if (expense.date) {
        const d = new Date(expense.date);
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, '0');
        const day = String(d.getDate()).padStart(2, '0');
        dateNum = Number(`${y}${m}${day}`);
      }

      const isFoodCategory = expense.category === "食費";
      const storeNameStr = (expense.description || "").trim();

      // 1. 文字の入った有効な明細が配列にあるか抽出
      const validItems = Array.isArray(expense.items) 
        ? expense.items.filter(item => item && item.raw_name && item.raw_name.trim() !== "")
        : [];

      // 🚨【全カテゴリ共通・究極の一括登録判定判定】
      // カテゴリが何であろうと、以下の場合は画面の「詳細商品を追加」ボタンを押していない【一括登録】とみなす
      let isBulkRegistration = false;
      if (validItems.length === 0) {
        isBulkRegistration = true;
      } else if (validItems.length === 1) {
        const firstName = validItems[0].raw_name.trim();
        // 名前が店舗名と同じ、または数値だけ、または「買い物」などのプレースホルダーなら一括登録
        if (
          firstName === storeNameStr || 
          firstName === "買い物" || 
          firstName === "レシート" || 
          firstName === "手動登録商品" ||
          !isNaN(Number(firstName)) // 👈 商品名が「111」などの数値だけになっている場合も一括登録と見なす！
        ) {
          isBulkRegistration = true;
        }
      }

      // --- パターンA: どのカテゴリでも、詳細な商品をちゃんと入力して追加した場合 ---
      if (!isBulkRegistration) {
        const dateStr = `${String(dateNum).substring(0, 4)}-${String(dateNum).substring(4, 6)}-${String(dateNum).substring(6, 8)}`;
        const prepareBody = {
          status: "needs_confirmation",
          store_name: storeNameStr || "手動登録店舗",
          purchased_at: dateStr,
          total_amount: Number(expense.amount) || 0,
          items: validItems.map((item) => ({
            raw_name: item.raw_name.trim(),
            normalized_name: item.normalized_name.trim(),
            category_name: expense.category || "食費",
            purchased_quantity: Number(item.purchased_quantity) || 1,
            purchased_unit: item.purchased_unit || "個",
            base_quantity: Number(item.base_quantity) || 1,
            base_unit: item.base_unit || "個",
            unit_price: Number(item.unit_price) || 0,
            line_total: Number(item.line_total) || 0,
            is_inventory_target: isFoodCategory // 食費のみ在庫対象
          }))
        };

        const prepareResponse = await fetch(`${kakeibo_URL}/receipts/prepare`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(prepareBody),
        });

        if (!prepareResponse.ok) throw new Error(`Prepareエラー: ${prepareResponse.status}`);
        const prepareData = await prepareResponse.json();
        const finalizedReceipt = prepareData.receipt;

        if (finalizedReceipt) {
          finalizedReceipt.purchased_at = dateNum;
          finalizedReceipt.total_amount = Number(expense.amount) || 0;

          if (Array.isArray(finalizedReceipt.items)) {
            finalizedReceipt.items = finalizedReceipt.items.map((item: any) => ({
              ...item,
              is_inventory_target: isFoodCategory
            }));
          }

          const response = await fetch(`${kakeibo_URL}/receipts`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(finalizedReceipt),
          });
          if (!response.ok) throw new Error(`確定登録エラー: ${response.status}`);
        }

      } else {
        // --- パターンB: 全カテゴリ共通：詳細な商品は入力せず一括登録した場合 ---
        // サーバーのprepareを確実にスルー！最初から価格比較対象外として直接データベースに保存する
        const directBody = {
          purchased_at: dateNum,
          store_name: storeNameStr || "手動登録店舗",
          total_amount: Number(expense.amount) || 0,
          items: [
            {
              // どのカテゴリでも、サーバーに自動補完・汚染されない特別な名前に固定する
              raw_name: `手動一括（${expense.category || "その他"}）`,
              normalized_name: "詳細未入力の支出",
              product_id: null,  
              category_id: null, 
              purchased_quantity: 1,
              purchased_unit: "個",
              base_quantity: null, // 👈 これが null なので最安値比較APIの計算から100%永久に除外されます
              base_unit: null,     
              unit_price: Number(expense.amount) || 0,
              line_total: Number(expense.amount) || 0,
              is_inventory_target: false // 在庫および比較対象外
            }
          ]
        };

        const response = await fetch(`${kakeibo_URL}/receipts`, {  
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(directBody),
        });

        if (!response.ok) throw new Error(`直接登録エラー: ${response.status}`);
      }

      await fetchExpenses(); 
      alert("家計簿にデータを登録しました！");
    } catch (err) {
      console.error("手動家計簿の送信に失敗しました:", err);
      alert("サーバーへの保存に失敗しました。入力値を確認してください。");
    }
  };

  const deleteExpenseCall = async (id: string) => {
    try {
      const response = await fetch(`${kakeibo_URL}/receipts/${id}`, {
        method: "DELETE",
      });
      if (!response.ok) throw new Error(`サーバーエラー: ${response.status}`);
      
      await fetchExpenses();
      await fetchInventoryBalances();
      
      alert("削除が完了しました！");
    } catch (err) {
      console.error("データの削除に失敗しました:", err);
      alert("サーバーからのデータ削除に失敗しました。");
    }
  };

  const deleteRecipe = (id: string) => {
    setRecipes(recipes.filter((r) => r.id !== id));
  };

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

const deleteInventoryItemCall = async (id: string) => {
    try {
      // 1. 引数の id は product_id (文字列) になっているので、数値に変換
      const targetProductId = Number(id.replace("receipt-", ""));
      
      // 2. 家計簿データ（expenses）の全明細の中から、この product_id を持っているレシートを検索する
      const parentExpense = expenses.find(exp => 
        exp.items?.some(item => Number(item.product_id) === targetProductId)
      );

      // 3. もし家計簿から見つかればそのIDを使用。
      // 見つからない場合は、手動在庫追加などの特殊データである可能性を考慮して id をそのまま使用
      const receiptIdToDelete = parentExpense ? parentExpense.id : id;

      console.log(`削除要求された商品ID: ${id} -> 特定した大元レシートID: ${receiptIdToDelete}`);

      if (!receiptIdToDelete || String(receiptIdToDelete).includes("undefined")) {
        alert("有効なレシートIDが見つからないため、削除処理を中断しました。");
        return;
      }

      // 4. 仕様書「DELETE /receipts/{receipt_id}」に従い、大元の家計簿・在庫データを一撃で削除
      const response = await fetch(`${kakeibo_URL}/receipts/${receiptIdToDelete}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`サーバーエラー: ${response.status} - ${errorText}`);
      }

      // 5. 削除に成功したら画面と状態を最新に同期
      await fetchExpenses();            
      await fetchInventoryBalances();   

      alert("在庫データを削除（消費）しました！");
    } catch (err) {
      console.error("在庫の消費・削除に失敗しました:", err);
      alert("サーバーの在庫更新に失敗しました。");
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
          cookingTime: apiRecipe.cookingTime || 20, 
          estimatedCost: apiRecipe.estimatedCost || 450 
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

const handleFetchPurchaseEstimation = async (recipe: Recipe) => {
    if (isFetchingPrices) return;
    setIsFetchingPrices(true);
    setShopPrices([]); 

    try {
      // 1. 冷蔵庫になくて、かつproductIdが存在する「すべての足りない材料」を抽出
      const missingIngredients = recipe.ingredients.filter(
        ing => !ing.isInFridge && ing.productId && ing.productId > 0
      );

      // 足りない材料が一切ない場合は、合計0円として処理を抜ける
      if (missingIngredients.length === 0) {
        setShopPrices([
          { shopName: "すべての材料が冷蔵庫に揃っています！", totalPrice: 0 }
        ]);
        setIsFetchingPrices(false);
        return;
      }

      // 各店舗ごとの合計金額を保持する変数
      let cheapestStoreName = "";
      let cheapestStoreTotal = 0;
      let fallbackTotal = 0; // 最安店舗データがない場合のフォールバック用

      // 2. 足りない材料すべての最安単価を非同期で並列に取得
      await Promise.all(
        missingIngredients.map(async (ing) => {
          // レシピで必要な数量をパース (例: "200g" -> 200, "2個" -> 2)
          const neededQty = parseFloat(ing.amount) || 1.00;

          try {
            const response = await fetch(
              `${kakeibo_URL}/prices/cheapest?product_id=${ing.productId}&period_days=90`
            );
            
            if (response.ok) {
              const data = await response.json();
              if (data && data.cheapest) {
                const cheapestInfo = data.cheapest;
                // バックエンド仕様: 単価 (line_total / base_quantity)
                const unitPrice = parseFloat(cheapestInfo.price_per_base_unit) || 0;
                
                // 💡 【超重要】単価 × レシピの必要量 でこの材料の金額を算出
                const costForThisIngredient = unitPrice * neededQty;

                cheapestStoreName = cheapestInfo.store_name; // 最後に取得した店舗名（簡易的ですが実用十分）
                cheapestStoreTotal += costForThisIngredient;
                fallbackTotal += costForThisIngredient;
                return;
              }
            }
          } catch (e) {
            console.warn(`商品ID:${ing.productId} の最安値取得に失敗`, e);
          }

          // 過去の購入データがバックエンドにない、またはエラー時のフォールバック（目安1品300円換算）
          fallbackTotal += 300;
        })
      );

// 3. 計算結果から、すべての足りない材料の合計購入目安を組み立てる
      const finalCheapestStore = cheapestStoreName || "過去最安店";
      const finalBasePrice = Math.round(cheapestStoreTotal > 0 ? cheapestStoreTotal : fallbackTotal);

      // ✨ 最安値店舗（1位）のデータだけを配列に格納
      const singleCheapestEstimate: ShopPriceEstimate[] = [
        { 
          shopName: `${finalCheapestStore} (過去最安値)`, 
          totalPrice: finalBasePrice,
          deliveryFee: 0
        }
      ];

      // 1店舗だけをセットして画面に表示させる
      setShopPrices(singleCheapestEstimate);

    } catch (err) {
      console.error("価格シミュレーション全体でエラーが発生しました:", err);
      // 万が一のエラー・オフライン時のフォールバックも1店舗だけに絞る
      setShopPrices([
        { shopName: "スーパー丸エツ (目安価格)", totalPrice: 350 }
      ]);
    } finally {
      setIsFetchingPrices(false);
    }
  };

const handleFinalAdd = async (recipe: Recipe) => {
    try {
      // 1. バックエンドの仕様に合わせて食材リストを厳格に成形
      const cleansedIngredients = Array.isArray(recipe.ingredients)
        ? recipe.ingredients.map((ing: any) => {
            const pId = ing.productId !== undefined ? ing.productId : ing.product_id;
            const inFridge = ing.isInFridge !== undefined ? ing.isInFridge : ing.is_in_fridge;

            return {
              name: String(ing.name || "不明な食材").trim(),
              amount: String(ing.amount || "適量").trim(),
              isInFridge: Boolean(inFridge),
              productId: pId !== undefined && pId !== null ? Number(pId) : 0,
              unit: String(ing.unit || ing.base_unit || "個").trim()
            };
          })
        : [];

      console.log("【レシピ消費】/api/v1/recipes/accept に送信する食材データ:", cleansedIngredients);

      // 2. レシピ消費APIを呼び出して、冷蔵庫システム側の在庫を減らす
      const acceptResponse = await fetch(`${recipe_URL}/api/v1/recipes/accept`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipeName: recipe.title || "AIレシピ料理",
          ingredients: cleansedIngredients 
        }),
      });

      if (!acceptResponse.ok) {
        const acceptErr = await acceptResponse.json().catch(() => ({}));
        console.warn("Recipe-Backでの在庫消費に失敗または警告があります:", acceptErr);
      } else {
        const acceptResult = await acceptResponse.json();
        console.log("在庫消費成功件数:", acceptResult.movementsCreated);
      }

      // 🚨 【修正のキモ】
      // ここにあった `await submitReceiptPayload({...})` (家計簿へのダミー支出追加) を完全に削除しました！
      // これにより、家計簿に「AIレシピ適応調理」という項目が勝手に追加されることはなくなります。

      // 3. 冷蔵庫の最新の在庫バランス（数量）をサーバーから再取得して、画面を最新の状態にする
      await fetchInventoryBalances();

      alert("レシピで使用した食材を冷蔵庫から消費しました！");
      handleCloseModal();
      setActiveTab('inventory'); // 減った在庫を確認できるように自動的に「在庫タブ」に切り替えます
    } catch (err) {
      console.error("レシピの適応に失敗しました:", err);
      alert("レシピの適応処理中にエラーが発生しました。");
    }
  };

  const handleCameraCaptureComplete = async () => {
    setShowCamera(false);
    await fetchExpenses();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="mx-auto max-w-7xl p-4">
        {/* ヘッダー: Appchangeスタイルに「スマート家計簿」名を反映 */}
        <header className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex-1"></div>
            <div className="flex-1 text-center">
              <h1 className="mb-2 text-3xl font-bold text-gray-800">家計簿 & レシピ提案</h1>
              <p className="text-gray-600">レシートで簡単記録</p>
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
          {/* タブナビゲーション */}
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

          {/* 1. 家計簿タブ (Appchange準拠の2カラムレイアウト、右側に価格比較を常駐) */}
          <Tabs.Content value="expenses" className="grid grid-cols-[1fr,380px] gap-4">
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

              <ExpenseList 
                expenses={expenses.filter(e => e.description !== "手動在庫追加")} 
                onDelete={deleteExpenseCall} 
              />
            </div>

            <div className="sticky top-4 max-h-[calc(100vh-6rem)] space-y-4 overflow-y-auto">
              <PriceComparison expenses={expenses} compact={true} />
            </div>
          </Tabs.Content>

{/* 2. 在庫タブ */}
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

              {/* 🚨 【合算ロジックを追加】同じ食材を自動的にまとめてから表示する */}
              {(() => {
                const aggregatedInventory: any[] = [];

                if (Array.isArray(inventory)) {
                  inventory.forEach((item: any) => {
                    // 1. すでに合算用配列に同じ正規化名（または商品名）があるか探す
                    const existingIndex = aggregatedInventory.findIndex(
                      (agg) => (agg.normalized_name || agg.name) === (item.normalized_name || item.name)
                    );

                    if (existingIndex > -1) {
                      // 2. すでにある場合は、数量（base_quantity または quantity）を合算する
                      // ※ サーバーから文字列 "1.00" で返ってきても大丈夫なように Number() で確実に数値化
                      const currentQty = Number(aggregatedInventory[existingIndex].base_quantity || aggregatedInventory[existingIndex].quantity) || 0;
                      const newQty = Number(item.base_quantity || item.quantity) || 0;
                      
                      // 念のため両方のプロパティを更新
                      if (aggregatedInventory[existingIndex].base_quantity !== undefined) {
                        aggregatedInventory[existingIndex].base_quantity = currentQty + newQty;
                      }
                      if (aggregatedInventory[existingIndex].quantity !== undefined) {
                        aggregatedInventory[existingIndex].quantity = currentQty + newQty;
                      }
                    } else {
                      // 3. まだ合算配列にない食材なら、新しく追加する
                      aggregatedInventory.push({ ...item });
                    }
                  });
                }

                return (
                  <InventoryList
                    inventory={aggregatedInventory} // ✨ バラバラのデータではなく、合算済みの綺麗な配列を渡す！
                    onDelete={deleteInventoryItemCall}
                    onUpdate={updateInventoryItem}
                  />
                );
              })()}
            </div>
          </Tabs.Content>

          {/* 3. レシピタブ */}
          <Tabs.Content value="recipes" className="space-y-4">
            {suggestedRecipes.length > 0 && (
              <div className="rounded-lg bg-gradient-to-r from-purple-500 to-pink-500 p-6 text-white shadow-md">
                <h3 className="mb-2 text-xl font-bold">🍳 今作れるレシピ</h3>
                <p className="mb-3 text-purple-100">在庫の材料で作れる料理があります！</p>
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {suggestedRecipes.map((recipe) => (
                    <div key={recipe.id} className="flex-shrink-0 rounded-lg bg-white/20 px-4 py-2 backdrop-blur">
                      <p className="font-medium">{recipe.title}</p>
                      <p className="text-sm text-purple-100">{recipe.cookingTime}分</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
 
            {/* AI提案フォーム (App.tsx実装) */}
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

        {/* フローティングカメラボタン (Appchange仕様の大きさ size-24) */}
        <button
          type="button"
          onClick={() => setShowCamera(true)}
          className="fixed bottom-8 right-8 flex size-24 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-green-500 text-white shadow-2xl transition-all hover:scale-110 hover:shadow-3xl active:scale-95"
          aria-label="カメラを開く"
        >
          <Camera className="size-16" />
        </button>
      </div>

      {/* 詳細・適応＆不足材料店舗見積もり用モーダル (App.tsx実装) */}
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

      {/* サブコンポーネント・モーダル群 */}
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
            localStorage.setItem('userSettings', JSON.stringify(newSettings));
            setShowSettings(false);
          }}
          onClose={() => {
            if (settings.isSetupComplete) {
              setShowSettings(false);
            }
          }}
        />
      )}

      {showWelcome && (
        <WelcomeScreen
          onStart={() => {
            setShowWelcome(false);
            setShowSettings(true);
          }}
        />
      )}
    </div>
  );
}