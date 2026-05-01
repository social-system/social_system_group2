import { format } from 'date-fns';
import { Calendar, Trash2, AlertCircle, Image as ImageIcon } from 'lucide-react';
import type { InventoryItem } from '../App';

interface InventoryListProps {
  inventory: InventoryItem[];
  onDelete: (id: string) => void;
  onUpdate: (id: string, updates: Partial<InventoryItem>) => void;
}

export function InventoryList({ inventory, onDelete, onUpdate }: InventoryListProps) {
  if (inventory.length === 0) {
    return (
      <div className="py-12 text-center text-gray-400">
        <p>まだ在庫がありません</p>
        <p className="text-sm">カメラ撮影または手動入力で追加してください</p>
      </div>
    );
  }

  const isExpiringSoon = (expiryDate?: Date) => {
    if (!expiryDate) return false;
    const daysUntilExpiry = Math.floor(
      (expiryDate.getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)
    );
    return daysUntilExpiry <= 3 && daysUntilExpiry >= 0;
  };

  const isExpired = (expiryDate?: Date) => {
    if (!expiryDate) return false;
    return expiryDate < new Date();
  };

  // カテゴリー別にグループ化
  const groupedInventory = inventory.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, InventoryItem[]>);

  return (
    <div className="space-y-4">
      {Object.entries(groupedInventory).map(([category, items]) => (
        <div key={category}>
          <h3 className="mb-2 font-bold text-gray-700">{category}</h3>
          <div className="space-y-2">
            {items.map((item) => (
              <div
                key={item.id}
                className={`flex items-center justify-between rounded-lg border p-4 transition-all hover:shadow-md ${
                  isExpired(item.expiryDate)
                    ? 'border-red-300 bg-red-50'
                    : isExpiringSoon(item.expiryDate)
                      ? 'border-yellow-300 bg-yellow-50'
                      : 'border-gray-200 bg-white'
                }`}
              >
                <div className="flex flex-1 items-center gap-4">
                  {item.imageUrl && (
                    <div className="size-12 flex-shrink-0 overflow-hidden rounded-lg bg-gray-200">
                      <img
                        src={item.imageUrl}
                        alt={item.name}
                        className="size-full object-cover"
                      />
                    </div>
                  )}
                  <div className="flex-1">
                    <div className="mb-1 flex items-center gap-2">
                      <p className="font-medium text-gray-800">{item.name}</p>
                      {isExpired(item.expiryDate) && (
                        <span className="flex items-center gap-1 rounded bg-red-200 px-2 py-0.5 text-xs font-medium text-red-800">
                          <AlertCircle className="size-3" />
                          期限切れ
                        </span>
                      )}
                      {isExpiringSoon(item.expiryDate) && !isExpired(item.expiryDate) && (
                        <span className="flex items-center gap-1 rounded bg-yellow-200 px-2 py-0.5 text-xs font-medium text-yellow-800">
                          <AlertCircle className="size-3" />
                          期限間近
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-gray-600">
                      <span>
                        数量: {item.quantity}
                        {item.unit}
                      </span>
                      {item.expiryDate && (
                        <span className="flex items-center gap-1">
                          <Calendar className="size-3" />
                          期限: {format(item.expiryDate, 'MM/dd')}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => onDelete(item.id)}
                  className="rounded-lg p-2 text-gray-400 transition-all hover:bg-red-100 hover:text-red-600 active:scale-95"
                >
                  <Trash2 className="size-5" />
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
