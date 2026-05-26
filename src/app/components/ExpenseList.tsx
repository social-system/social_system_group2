import { format } from 'date-fns';
import { Calendar, Trash2, Store, ShoppingBag } from 'lucide-react';
import type { Expense } from '../App';

interface ExpenseListProps {
  expenses: Expense[];
  onDelete: (id: string) => void;
}

export function ExpenseList({ expenses, onDelete }: ExpenseListProps) {
  if (expenses.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400">
        <p>まだ支出の記録がありません</p>
        <p className="text-sm">レシート撮影または手動入力で追加してください</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {expenses.map((expense) => (
        <div
          key={expense.id}
          className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 p-4 transition-all hover:border-blue-300 hover:shadow-md"
        >
          <div className="flex flex-1 items-center gap-4">
            {expense.imageUrl && (
              <div className="size-12 flex-shrink-0 overflow-hidden rounded-lg bg-gray-200">
                <img
                  src={expense.imageUrl}
                  alt="Receipt"
                  className="size-full object-cover"
                />
              </div>
            )}
            <div className="flex-1">
              <div className="mb-1 flex items-center gap-2">
                <span className="rounded bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
                  {expense.category}
                </span>
                <span className="flex items-center gap-1 text-xs text-gray-500">
                  <Calendar className="size-3" />
                  {format(expense.date, 'MM/dd')}
                </span>
                {expense.storeName && (
                  <span className="flex items-center gap-1 rounded bg-orange-100 px-2 py-1 text-xs font-medium text-orange-700">
                    <Store className="size-3" />
                    {expense.storeName}
                  </span>
                )}
              </div>
              <p className="text-gray-700">{expense.description}</p>
              {expense.items && expense.items.length > 0 && (
                <div className="mt-2 flex items-center gap-1 text-xs text-gray-500">
                  <ShoppingBag className="size-3" />
                  <span>
                    {expense.items.length}品目: {expense.items.map((item) => item.name).join(', ')}
                  </span>
                </div>
              )}
            </div>
          </div>
          <div className="flex items-center gap-4">
            <p className="text-xl font-bold text-gray-800">¥{expense.amount.toLocaleString()}</p>
            <button
              onClick={() => onDelete(expense.id)}
              className="rounded-lg p-2 text-gray-400 transition-all hover:bg-red-100 hover:text-red-600 active:scale-95"
            >
              <Trash2 className="size-5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}