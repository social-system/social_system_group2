import { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import type { Expense, PurchaseItem } from '../App';

interface AddExpenseFormProps {
  onAdd: (expense: Omit<Expense, 'id'>) => void;
  onClose: () => void;
}

export function AddExpenseForm({ onAdd, onClose }: AddExpenseFormProps) {
  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('食費');
  const [description, setDescription] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [storeName, setStoreName] = useState('');
  const [items, setItems] = useState<PurchaseItem[]>([]);
  const [showItemForm, setShowItemForm] = useState(false);

  //商品追加用のState
  const [itemName, setItemName] = useState('');
  const [itemPrice, setItemPrice] = useState('');
  const [itemQuantity, setItemQuantity] = useState('');
  const [itemUnit, setItemUnit] = useState('個');

  const categories = ['食費', '交通費', '娯楽', '光熱費', '医療', '衣類', 'その他'];
  const units = ['個', 'パック', '本', 'kg', 'g', 'L', 'ml', '袋', '缶'];

    const addItem = () => {
    if (!itemName || !itemPrice || !itemQuantity) return;

    const newItem: PurchaseItem = {
      name: itemName,
      price: parseFloat(itemPrice),
      quantity: parseFloat(itemQuantity),
      unit: itemUnit,
    };

    setItems([...items, newItem]);
    setItemName('');
    setItemPrice('');
    setItemQuantity('');
    setItemUnit('個');
    setShowItemForm(false);

    // 合計金額を自動計算
    const total = [...items, newItem].reduce((sum, item) => sum + item.price, 0);
    setAmount(total.toString());
  };

  const removeItem = (index: number) => {
    const newItems = items.filter((_, i) => i !== index);
    setItems(newItems);
    // 合計金額を再計算
    const total = newItems.reduce((sum, item) => sum + item.price, 0);
    setAmount(total > 0 ? total.toString() : '');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!amount || !description) return;

    onAdd({
      amount: parseFloat(amount),
      category,
      description,
      date: new Date(date),
      storeName: storeName || undefined,
      items: items.length > 0 ? items : undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-xl font-bold text-gray-800">支出を追加</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 transition-all hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="size-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">金額</label>
            <input
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="3500"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">カテゴリー</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">説明</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="スーパーでの買い物"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">日付</label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              店舗名（任意）
            </label>
            <input
              type="text"
              value={storeName}
              onChange={(e) => setStoreName(e.target.value)}
              placeholder="スーパーA"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="mt-1 text-xs text-gray-500">
              店舗名を入力すると価格比較機能が使えます
            </p>
          </div>

          {/* 購入商品リスト */}
          {items.length > 0 && (
            <div className="mb-4">
              <label className="mb-2 block text-sm font-medium text-gray-700">購入商品</label>
              <div className="space-y-2">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between rounded-lg bg-blue-50 p-3"
                  >
                    <div>
                      <p className="font-medium text-gray-800">{item.name}</p>
                      <p className="text-sm text-gray-600">
                        {item.quantity}
                        {item.unit} - ¥{item.price}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeItem(index)}
                      className="rounded-lg p-1 text-red-500 hover:bg-red-100"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 商品追加フォーム */}
          {showItemForm ? (
            <div className="mb-4 rounded-lg border border-blue-300 bg-blue-50 p-4">
              <h4 className="mb-3 font-medium text-gray-800">商品を追加</h4>
              <div className="mb-3">
                <input
                  type="text"
                  value={itemName}
                  onChange={(e) => setItemName(e.target.value)}
                  placeholder="商品名"
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
              <div className="mb-3 flex gap-2">
                <input
                  type="number"
                  value={itemPrice}
                  onChange={(e) => setItemPrice(e.target.value)}
                  placeholder="価格"
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <input
                  type="number"
                  step="0.01"
                  value={itemQuantity}
                  onChange={(e) => setItemQuantity(e.target.value)}
                  placeholder="数量"
                  className="w-20 rounded-lg border border-gray-300 px-3 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <select
                  value={itemUnit}
                  onChange={(e) => setItemUnit(e.target.value)}
                  className="w-20 rounded-lg border border-gray-300 px-2 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  {units.map((u) => (
                    <option key={u} value={u}>
                      {u}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowItemForm(false)}
                  className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  キャンセル
                </button>
                <button
                  type="button"
                  onClick={addItem}
                  className="flex-1 rounded-lg bg-blue-500 px-3 py-2 text-sm text-white hover:bg-blue-600"
                >
                  追加
                </button>
              </div>
            </div>
          ) : (
            <div className="mb-6">
              <button
                type="button"
                onClick={() => setShowItemForm(true)}
                className="flex w-full items-center justify-center gap-2 rounded-lg border-2 border-dashed border-gray-300 px-4 py-3 text-sm text-gray-600 transition-all hover:border-blue-400 hover:bg-blue-50 hover:text-blue-600"
              >
                <Plus className="size-4" />
                商品を追加（任意）
              </button>
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 transition-all hover:bg-gray-50 active:scale-95"
            >
              キャンセル
            </button>
            <button
              type="submit"
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-500 px-4 py-2 font-medium text-white transition-all hover:bg-blue-600 active:scale-95"
            >
              <Plus className="size-5" />
              追加
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
