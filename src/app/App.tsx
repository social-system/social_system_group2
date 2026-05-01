import { useState } from 'react';
import { Camera, Receipt, ChefHat, Plus, Package } from 'lucide-react';
import * as Tabs from '@radix-ui/react-tabs';
import { UniversalCamera } from './components/UniversalCamera';
import { ExpenseList } from './components/ExpenseList';
import { InventoryList } from './components/InventoryList';
import { RecipeList } from './components/RecipeList';
import { AddExpenseForm } from './components/AddExpenseForm';
import { AddInventoryForm } from './components/AddInventoryForm';
import { AddRecipeForm } from './components/AddRecipeForm';

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
  ingredients: string[];
  instructions: string;
  imageUrl?: string;
  cookingTime: number;
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

export default function App() {
  const [expenses, setExpenses] = useState<Expense[]>([
    {
      id: '1',
      amount: 3500,
      category: '食費',
      description: 'スーパーでの買い物',
      date: new Date(2026, 3, 27),
    },
    {
      id: '2',
      amount: 1200,
      category: '交通費',
      description: '電車代',
      date: new Date(2026, 3, 28),
    },
  ]);

  const [recipes, setRecipes] = useState<Recipe[]>([
    {
      id: '1',
      title: 'カレーライス',
      ingredients: ['玉ねぎ', 'にんじん', 'じゃがいも', '豚肉', 'カレールー'],
      instructions: '野菜と肉を炒めて、水を加えて煮込む。カレールーを入れて溶かす。',
      cookingTime: 30,
    },
    {
      id: '2',
      title: '野菜炒め',
      ingredients: ['キャベツ', 'にんじん', '豚肉'],
      instructions: '野菜と肉を強火で炒める。塩コショウで味付けする。',
      cookingTime: 15,
    },
    {
      id: '3',
      title: 'トマトパスタ',
      ingredients: ['パスタ', 'トマト', '玉ねぎ', 'にんにく'],
      instructions: 'パスタを茹でる。トマトソースを作って和える。',
      cookingTime: 20,
    },
  ]);

  const [inventory, setInventory] = useState<InventoryItem[]>([
    {
      id: '1',
      name: '玉ねぎ',
      quantity: 3,
      unit: '個',
      category: '野菜',
      expiryDate: new Date(2026, 4, 5),
    },
    {
      id: '2',
      name: 'にんじん',
      quantity: 2,
      unit: '本',
      category: '野菜',
    },
    {
      id: '3',
      name: '豚肉',
      quantity: 300,
      unit: 'g',
      category: '肉類',
      expiryDate: new Date(2026, 4, 1),
    },
  ]);

  const [showCamera, setShowCamera] = useState(false);
  const [showAddExpense, setShowAddExpense] = useState(false);
  const [showAddInventory, setShowAddInventory] = useState(false);
  const [showAddRecipe, setShowAddRecipe] = useState(false);

  const addExpense = (expense: Omit<Expense, 'id'>) => {
    const newExpense = { ...expense, id: Date.now().toString() };
    setExpenses([newExpense, ...expenses]);
  };

  const deleteExpense = (id: string) => {
    setExpenses(expenses.filter((e) => e.id !== id));
  };

  const addRecipe = (recipe: Omit<Recipe, 'id'>) => {
    const newRecipe = { ...recipe, id: Date.now().toString() };
    setRecipes([newRecipe, ...recipes]);
  };

  const deleteRecipe = (id: string) => {
    setRecipes(recipes.filter((r) => r.id !== id));
  };

  const addInventoryItem = (item: Omit<InventoryItem, 'id'>) => {
    const newItem = { ...item, id: Date.now().toString() };
    setInventory([newItem, ...inventory]);
  };

  const deleteInventoryItem = (id: string) => {
    setInventory(inventory.filter((i) => i.id !== id));
  };

  const updateInventoryItem = (id: string, updates: Partial<InventoryItem>) => {
    setInventory(inventory.map((item) => (item.id === id ? { ...item, ...updates } : item)));
  };

  const totalExpenses = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  // レシピ提案: 在庫にある材料で作れるレシピを表示
  const getSuggestedRecipes = () => {
    const inventoryNames = inventory.map((item) => item.name.toLowerCase());
    return recipes.filter((recipe) => {
      const requiredIngredients = recipe.ingredients.map((ing) => ing.toLowerCase());
      const availableCount = requiredIngredients.filter((ing) =>
        inventoryNames.some((inv) => inv.includes(ing) || ing.includes(inv))
      ).length;
      return availableCount >= requiredIngredients.length * 0.6; // 60%以上の材料があれば提案
    });
  };

  const suggestedRecipes = getSuggestedRecipes();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      <div className="mx-auto max-w-4xl p-4">
        <header className="mb-6 text-center">
          <h1 className="mb-2 text-4xl font-bold text-gray-800">💰 家計簿 & レシピ</h1>
          <p className="text-gray-600">カメラで簡単記録</p>
        </header>

        <Tabs.Root defaultValue="expenses" className="w-full">
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
                  onClick={() => setShowAddExpense(true)}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-3 font-medium text-white shadow-md transition-all hover:bg-blue-600 active:scale-95"
                >
                  <Plus className="size-5" />
                  手動入力
                </button>
              </div>

              <ExpenseList expenses={expenses} onDelete={deleteExpense} />
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
                  onClick={() => setShowAddInventory(true)}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-green-500 px-4 py-3 font-medium text-white shadow-md transition-all hover:bg-green-600 active:scale-95"
                >
                  <Plus className="size-5" />
                  手動入力
                </button>
              </div>

              <InventoryList
                inventory={inventory}
                onDelete={deleteInventoryItem}
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

            <div className="rounded-lg bg-white p-6 shadow-md">
              <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold text-gray-800">全レシピ</h2>
                <p className="text-gray-500">{recipes.length}件</p>
              </div>

              <div className="mb-4">
                <button
                  onClick={() => setShowAddRecipe(true)}
                  className="flex w-full items-center justify-center gap-2 rounded-lg bg-purple-500 px-4 py-3 font-medium text-white shadow-md transition-all hover:bg-purple-600 active:scale-95"
                >
                  <Plus className="size-5" />
                  レシピ追加
                </button>
              </div>

              <RecipeList recipes={recipes} onDelete={deleteRecipe} inventory={inventory} />
            </div>
          </Tabs.Content>
        </Tabs.Root>

        {/* フローティングカメラボタン */}
        <button
          onClick={() => setShowCamera(true)}
          className="fixed bottom-8 right-8 flex size-16 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-green-500 text-white shadow-2xl transition-all hover:scale-110 hover:shadow-3xl active:scale-95"
          aria-label="カメラを開く"
        >
          <Camera className="size-8" />
        </button>
      </div>

      {showCamera && (
        <UniversalCamera
          onCapture={(imageUrl, extractedData) => {
            setShowCamera(false);
            // 抽出されたデータを自動追加
            if (extractedData.expense) {
              addExpense(extractedData.expense);
            }
            if (extractedData.inventoryItems) {
              extractedData.inventoryItems.forEach((item) => addInventoryItem(item));
            }
          }}
          onClose={() => setShowCamera(false)}
        />
      )}

      {showAddInventory && (
        <AddInventoryForm
          onAdd={(item) => {
            addInventoryItem(item);
            setShowAddInventory(false);
          }}
          onClose={() => setShowAddInventory(false)}
        />
      )}

      {showAddExpense && (
        <AddExpenseForm
          onAdd={(expense) => {
            addExpense(expense);
            setShowAddExpense(false);
          }}
          onClose={() => setShowAddExpense(false)}
        />
      )}

      {showAddRecipe && (
        <AddRecipeForm
          onAdd={(recipe) => {
            addRecipe(recipe);
            setShowAddRecipe(false);
          }}
          onClose={() => setShowAddRecipe(false)}
        />
      )}
    </div>
  );
}
