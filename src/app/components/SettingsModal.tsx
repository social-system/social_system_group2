import { useState } from 'react';
import { X, Check, Plus, Trash2 } from 'lucide-react';
import type { UserSettings } from '../App';

interface SettingsModalProps {
  settings: UserSettings;
  onSave: (settings: UserSettings) => void;
  onClose: () => void;
}

const COMMON_STAPLES = [
  '醤油', '塩', '砂糖', '味噌', '酢', 'みりん', '料理酒',
  'サラダ油', 'ごま油', 'こしょう', '小麦粉', '片栗粉',
  'だしの素', 'コンソメ', '鶏がらスープの素',
];

const COMMON_INGREDIENTS = [
  '豚肉', '鶏肉', '牛肉', '魚', 'エビ', 'イカ',
  '玉ねぎ', 'にんじん', 'じゃがいも', 'キャベツ', 'トマト',
  '卵', '豆腐', '納豆', 'チーズ', 'ヨーグルト',
  'ご飯', 'パン', 'パスタ', 'うどん', 'そば',
];

export function SettingsModal({ settings, onSave, onClose }: SettingsModalProps) {
  const [selectedStaples, setSelectedStaples] = useState<string[]>(settings.staples);
  const [likedIngredients, setLikedIngredients] = useState<string[]>(settings.likedIngredients);
  const [dislikedIngredients, setDislikedIngredients] = useState<string[]>(settings.dislikedIngredients);
  const [customStaple, setCustomStaple] = useState('');
  const [customLiked, setCustomLiked] = useState('');
  const [customDisliked, setCustomDisliked] = useState('');

  const isInitialSetup = !settings.isSetupComplete;

  const toggleStaple = (staple: string) => {
    if (selectedStaples.includes(staple)) {
      setSelectedStaples(selectedStaples.filter((s) => s !== staple));
    } else {
      setSelectedStaples([...selectedStaples, staple]);
    }
  };

  const toggleLiked = (ingredient: string) => {
    if (likedIngredients.includes(ingredient)) {
      setLikedIngredients(likedIngredients.filter((i) => i !== ingredient));
    } else {
      setLikedIngredients([...likedIngredients, ingredient]);
      // 嫌いなものリストから削除
      setDislikedIngredients(dislikedIngredients.filter((i) => i !== ingredient));
    }
  };

  const toggleDisliked = (ingredient: string) => {
    if (dislikedIngredients.includes(ingredient)) {
      setDislikedIngredients(dislikedIngredients.filter((i) => i !== ingredient));
    } else {
      setDislikedIngredients([...dislikedIngredients, ingredient]);
      // 好きなものリストから削除
      setLikedIngredients(likedIngredients.filter((i) => i !== ingredient));
    }
  };

  const addCustomStaple = () => {
    if (customStaple.trim() && !selectedStaples.includes(customStaple.trim())) {
      setSelectedStaples([...selectedStaples, customStaple.trim()]);
      setCustomStaple('');
    }
  };

  const addCustomLiked = () => {
    if (customLiked.trim() && !likedIngredients.includes(customLiked.trim())) {
      setLikedIngredients([...likedIngredients, customLiked.trim()]);
      setCustomLiked('');
    }
  };

  const addCustomDisliked = () => {
    if (customDisliked.trim() && !dislikedIngredients.includes(customDisliked.trim())) {
      setDislikedIngredients([...dislikedIngredients, customDisliked.trim()]);
      setCustomDisliked('');
    }
  };

  const handleSave = () => {
    onSave({
      staples: selectedStaples,
      likedIngredients,
      dislikedIngredients,
      isSetupComplete: true,
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4 overflow-y-auto">
      <div className="my-8 w-full max-w-3xl rounded-lg bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-gray-200 p-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              {isInitialSetup ? '初期設定' : '設定'}
            </h2>
            {isInitialSetup && (
              <p className="mt-1 text-sm text-gray-600">
                よく使う調味料と食材の好みを設定してください
              </p>
            )}
          </div>
          {!isInitialSetup && (
            <button
              onClick={onClose}
              className="rounded-lg p-1 text-gray-400 transition-all hover:bg-gray-100 hover:text-gray-600"
            >
              <X className="size-6" />
            </button>
          )}
        </div>

        <div className="max-h-[70vh] overflow-y-auto p-6">
          {/* 常備調味料 */}
          <section className="mb-6">
            <h3 className="mb-3 text-lg font-bold text-gray-800">🧂 常備調味料</h3>
            <p className="mb-3 text-sm text-gray-600">
              いつも家にある調味料を選択してください。レシピ提案時に考慮されます。
            </p>
            <div className="mb-3 flex flex-wrap gap-2">
              {COMMON_STAPLES.map((staple) => (
                <button
                  key={staple}
                  onClick={() => toggleStaple(staple)}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    selectedStaples.includes(staple)
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {selectedStaples.includes(staple) && '✓ '}
                  {staple}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={customStaple}
                onChange={(e) => setCustomStaple(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustomStaple()}
                placeholder="その他の調味料を追加"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={addCustomStaple}
                className="rounded-lg bg-blue-500 px-4 py-2 text-white transition-all hover:bg-blue-600"
              >
                <Plus className="size-5" />
              </button>
            </div>
            {selectedStaples.filter((s) => !COMMON_STAPLES.includes(s)).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedStaples
                  .filter((s) => !COMMON_STAPLES.includes(s))
                  .map((staple) => (
                    <span
                      key={staple}
                      className="flex items-center gap-1 rounded-lg bg-blue-100 px-3 py-1 text-sm text-blue-800"
                    >
                      {staple}
                      <button
                        onClick={() => setSelectedStaples(selectedStaples.filter((s) => s !== staple))}
                        className="ml-1 text-blue-600 hover:text-blue-800"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
              </div>
            )}
          </section>

          {/* 好きな食材 */}
          <section className="mb-6">
            <h3 className="mb-3 text-lg font-bold text-gray-800">❤️ 好きな食材</h3>
            <p className="mb-3 text-sm text-gray-600">
              好きな食材を選択すると、それを使ったレシピを優先的に提案します。
            </p>
            <div className="mb-3 flex flex-wrap gap-2">
              {COMMON_INGREDIENTS.map((ingredient) => (
                <button
                  key={ingredient}
                  onClick={() => toggleLiked(ingredient)}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    likedIngredients.includes(ingredient)
                      ? 'bg-green-500 text-white'
                      : dislikedIngredients.includes(ingredient)
                        ? 'bg-gray-100 text-gray-400 line-through'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {likedIngredients.includes(ingredient) && '❤️ '}
                  {ingredient}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={customLiked}
                onChange={(e) => setCustomLiked(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustomLiked()}
                placeholder="その他の好きな食材を追加"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-green-500 focus:outline-none focus:ring-1 focus:ring-green-500"
              />
              <button
                onClick={addCustomLiked}
                className="rounded-lg bg-green-500 px-4 py-2 text-white transition-all hover:bg-green-600"
              >
                <Plus className="size-5" />
              </button>
            </div>
            {likedIngredients.filter((i) => !COMMON_INGREDIENTS.includes(i)).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {likedIngredients
                  .filter((i) => !COMMON_INGREDIENTS.includes(i))
                  .map((ingredient) => (
                    <span
                      key={ingredient}
                      className="flex items-center gap-1 rounded-lg bg-green-100 px-3 py-1 text-sm text-green-800"
                    >
                      {ingredient}
                      <button
                        onClick={() => setLikedIngredients(likedIngredients.filter((i) => i !== ingredient))}
                        className="ml-1 text-green-600 hover:text-green-800"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
              </div>
            )}
          </section>

          {/* 嫌いな食材 */}
          <section className="mb-6">
            <h3 className="mb-3 text-lg font-bold text-gray-800">🚫 嫌いな食材</h3>
            <p className="mb-3 text-sm text-gray-600">
              嫌いな食材を選択すると、それを含むレシピは提案されません。
            </p>
            <div className="mb-3 flex flex-wrap gap-2">
              {COMMON_INGREDIENTS.map((ingredient) => (
                <button
                  key={ingredient}
                  onClick={() => toggleDisliked(ingredient)}
                  className={`rounded-lg px-3 py-2 text-sm font-medium transition-all ${
                    dislikedIngredients.includes(ingredient)
                      ? 'bg-red-500 text-white'
                      : likedIngredients.includes(ingredient)
                        ? 'bg-gray-100 text-gray-400'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {dislikedIngredients.includes(ingredient) && '🚫 '}
                  {ingredient}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={customDisliked}
                onChange={(e) => setCustomDisliked(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && addCustomDisliked()}
                placeholder="その他の嫌いな食材を追加"
                className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-red-500 focus:outline-none focus:ring-1 focus:ring-red-500"
              />
              <button
                onClick={addCustomDisliked}
                className="rounded-lg bg-red-500 px-4 py-2 text-white transition-all hover:bg-red-600"
              >
                <Plus className="size-5" />
              </button>
            </div>
            {dislikedIngredients.filter((i) => !COMMON_INGREDIENTS.includes(i)).length > 0 && (
              <div className="mt-2 flex flex-wrap gap-2">
                {dislikedIngredients
                  .filter((i) => !COMMON_INGREDIENTS.includes(i))
                  .map((ingredient) => (
                    <span
                      key={ingredient}
                      className="flex items-center gap-1 rounded-lg bg-red-100 px-3 py-1 text-sm text-red-800"
                    >
                      {ingredient}
                      <button
                        onClick={() => setDislikedIngredients(dislikedIngredients.filter((i) => i !== ingredient))}
                        className="ml-1 text-red-600 hover:text-red-800"
                      >
                        <X className="size-3" />
                      </button>
                    </span>
                  ))}
              </div>
            )}
          </section>
        </div>

        <div className="border-t border-gray-200 p-6">
          <button
            onClick={handleSave}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-blue-500 to-green-500 px-6 py-3 font-medium text-white shadow-md transition-all hover:from-blue-600 hover:to-green-600 active:scale-95"
          >
            <Check className="size-5" />
            {isInitialSetup ? '設定を完了' : '保存'}
          </button>
          {isInitialSetup && (
            <p className="mt-2 text-center text-sm text-gray-500">
              後から設定アイコンで変更できます
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
