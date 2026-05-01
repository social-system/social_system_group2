import { useState } from 'react';
import { X, Plus } from 'lucide-react';
import type { Recipe } from '../App';

interface AddRecipeFormProps {
  onAdd: (recipe: Omit<Recipe, 'id'>) => void;
  onClose: () => void;
}

export function AddRecipeForm({ onAdd, onClose }: AddRecipeFormProps) {
  const [title, setTitle] = useState('');
  const [ingredients, setIngredients] = useState('');
  const [instructions, setInstructions] = useState('');
  const [cookingTime, setCookingTime] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !ingredients || !instructions || !cookingTime) return;

    onAdd({
      title,
      ingredients: ingredients.split(',').map((item) => item.trim()),
      instructions,
      cookingTime: parseInt(cookingTime),
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-4">
          <h2 className="text-xl font-bold text-gray-800">レシピを追加</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-gray-400 transition-all hover:bg-gray-100 hover:text-gray-600"
          >
            <X className="size-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4">
          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">料理名</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="カレーライス"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              材料（カンマ区切り）
            </label>
            <input
              type="text"
              value={ingredients}
              onChange={(e) => setIngredients(e.target.value)}
              placeholder="玉ねぎ, にんじん, じゃがいも"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-gray-700">調理時間（分）</label>
            <input
              type="number"
              value={cookingTime}
              onChange={(e) => setCookingTime(e.target.value)}
              placeholder="30"
              required
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
            />
          </div>

          <div className="mb-6">
            <label className="mb-1 block text-sm font-medium text-gray-700">作り方</label>
            <textarea
              value={instructions}
              onChange={(e) => setInstructions(e.target.value)}
              placeholder="野菜と肉を炒めて、水を加えて煮込む..."
              required
              rows={4}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
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
              className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-purple-500 px-4 py-2 font-medium text-white transition-all hover:bg-purple-600 active:scale-95"
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
