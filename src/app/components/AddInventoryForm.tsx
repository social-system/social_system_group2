import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import type { InventoryItem } from '../App';

interface AddInventoryFormProps {
  onAdd: (item: Omit<InventoryItem, 'id'>) => void;
  onClose: () => void;
}

export function AddInventoryForm({ onAdd, onClose }: AddInventoryFormProps) {
  const [name, setName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [unit, setUnit] = useState('個');
  const [category, setCategory] = useState('食品');
  const [expiryDate, setExpiryDate] = useState('');

  const units = ['個', 'パック', '本', 'kg', 'g', 'L', 'ml', '袋', '缶'];
  const categories = ['食品', '野菜', '肉類', '魚類', '調味料', '飲料', '日用品', 'その他'];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !quantity) return;

    onAdd({
      name,
      quantity: parseFloat(quantity),
      unit,
      category,
      expiryDate: expiryDate ? new Date(expiryDate) : undefined,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-xl font-bold text-gray-800">在庫を追加</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 transition-all hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="size-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">商品名</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="玉ねぎ"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            />
          </div>

          <div className="mb-4 flex gap-4">
            <div className="flex-1">
              <label className="mb-1 block text-sm font-medium text-gray-700">数量</label>
              <input
                type="number"
                step="1"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="3"
                required
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              />
            </div>
            <div className="flex-1">
              <label className="mb-1 block text-sm font-medium text-gray-700">単位</label>
              <select
                value={unit}
                onChange={(e) => setUnit(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              >
                {units.map((u) => (
                  <option key={u} value={u}>
                    {u}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">カテゴリー</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              賞味期限 (任意)
            </label>
            <input
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
            />
          </div>

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
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-500 px-4 py-2 font-medium text-white transition-all hover:bg-green-600 active:scale-95"
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
