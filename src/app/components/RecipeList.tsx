import { Clock, Trash2, CheckCircle, AlertCircle } from 'lucide-react';
import type { Recipe, InventoryItem } from '../App';

interface RecipeListProps {
  recipes: Recipe[];
  onDelete: (id: string) => void;
  inventory: InventoryItem[];
}

export function RecipeList({ recipes, onDelete, inventory }: RecipeListProps) {
  if (recipes.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400">
        <p>まだレシピがありません</p>
        <p className="text-sm">レシピ追加で登録してください</p>
      </div>
    );
  }

  const checkIngredientAvailability = (recipe: Recipe) => {
    const inventoryNames = inventory.map((item) => item.name.toLowerCase());
    const requiredIngredients = recipe.ingredients.map((ing) => ing.toLowerCase());

    const availableIngredients = requiredIngredients.filter((ing) =>
      inventoryNames.some((inv) => inv.includes(ing) || ing.includes(inv))
    );

    const availabilityPercentage = (availableIngredients.length / requiredIngredients.length) * 100;

    return {
      canMake: availabilityPercentage >= 60,
      percentage: Math.round(availabilityPercentage),
      availableCount: availableIngredients.length,
      totalCount: requiredIngredients.length,
    };
  };

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {recipes.map((recipe) => {
        const availability = checkIngredientAvailability(recipe);
        const inventoryNames = inventory.map((item) => item.name.toLowerCase());

        return (
          <div
            key={recipe.id}
            className={`overflow-hidden rounded-lg border shadow-sm transition-all hover:shadow-md ${
              availability.canMake
                ? 'border-green-300 bg-green-50/30'
                : 'border-gray-200 bg-white'
            }`}
          >
            {recipe.imageUrl && (
              <div className="h-48 overflow-hidden bg-gray-200">
                <img
                  src={recipe.imageUrl}
                  alt={recipe.title}
                  className="size-full object-cover"
                />
              </div>
            )}
            <div className="p-4">
              <div className="mb-2 flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-800">{recipe.title}</h3>
                  {availability.canMake ? (
                    <div className="mt-1 flex items-center gap-1 text-sm text-green-700">
                      <CheckCircle className="size-4" />
                      <span>今すぐ作れます！</span>
                    </div>
                  ) : (
                    <div className="mt-1 flex items-center gap-1 text-sm text-gray-500">
                      <AlertCircle className="size-4" />
                      <span>
                        材料 {availability.availableCount}/{availability.totalCount}
                      </span>
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onDelete(recipe.id)}
                  className="rounded-lg p-1 text-gray-400 transition-all hover:bg-red-100 hover:text-red-600 active:scale-95"
                >
                  <Trash2 className="size-4" />
                </button>
              </div>

              <div className="mb-3 flex items-center gap-1 text-sm text-gray-600">
                <Clock className="size-4" />
                <span>{recipe.cookingTime}分</span>
              </div>

              <div className="mb-3">
                <p className="mb-1 text-sm font-medium text-gray-700">材料:</p>
                <div className="flex flex-wrap gap-1">
                  {recipe.ingredients.map((ingredient, idx) => {
                    const hasIngredient = inventoryNames.some(
                      (inv) => inv.includes(ingredient.toLowerCase()) || ingredient.toLowerCase().includes(inv)
                    );
                    return (
                      <span
                        key={idx}
                        className={`rounded px-2 py-1 text-xs ${
                          hasIngredient
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {hasIngredient && '✓ '}
                        {ingredient}
                      </span>
                    );
                  })}
                </div>
              </div>

              <div>
                <p className="mb-1 text-sm font-medium text-gray-700">作り方:</p>
                <p className="text-sm text-gray-600">{recipe.instructions}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
