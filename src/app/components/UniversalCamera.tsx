import { useRef, useState, useEffect } from 'react';
import { Camera, X, Check, Sparkles } from 'lucide-react';
import type { Expense, InventoryItem } from '../App';

interface ExtractedData {
  expense?: Omit<Expense, 'id'>;
  inventoryItems?: Omit<InventoryItem, 'id'>[];
}

interface UniversalCameraProps {
  onCapture: (imageUrl: string, extractedData: ExtractedData) => void;
  onClose: () => void;
}

export function UniversalCamera({ onCapture, onClose }: UniversalCameraProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [extractedData, setExtractedData] = useState<ExtractedData>({});

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, []);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      setError('カメラへのアクセスが拒否されました');
      console.error('Camera error:', err);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }
  };

  // モックOCR/画像認識関数
  const analyzeImage = async (imageUrl: string): Promise<ExtractedData> => {
    // 実際のアプリでは、ここでOCR APIや画像認識APIを呼び出します
    // 例: Google Cloud Vision API, Azure Computer Vision, Tesseract.js など

    return new Promise((resolve) => {
      setTimeout(() => {
        // ランダムでレシートまたは在庫を検出するモック
        const isReceipt = Math.random() > 0.5;

        if (isReceipt) {
          // レシートを検出した場合
          const stores = ['スーパーA', 'スーパーB', 'スーパーC', '八百屋', 'ドラッグストア'];
          const storeName = stores[Math.floor(Math.random() * stores.length)];

          const purchaseItems = [
            { name: '牛乳', price: 198, quantity: 1, unit: 'パック' },
            { name: '卵', price: 248, quantity: 1, unit: 'パック' },
            { name: 'パン', price: 158, quantity: 1, unit: '個' },
            { name: 'トマト', price: 298, quantity: 3, unit: '個' },
            { name: 'キャベツ', price: 178, quantity: 1, unit: '個' },
            { name: '玉ねぎ', price: 120, quantity: 3, unit: '個' },
            { name: 'にんじん', price: 98, quantity: 2, unit: '本' },
          ];

          // ランダムに2-4個の商品を選択
          const numItems = Math.floor(Math.random() * 3) + 2;
          const selectedItems = [];
          const usedIndices = new Set<number>();

          while (selectedItems.length < numItems) {
            const randomIndex = Math.floor(Math.random() * purchaseItems.length);
            if (!usedIndices.has(randomIndex)) {
              selectedItems.push(purchaseItems[randomIndex]);
              usedIndices.add(randomIndex);
            }
          }

          const totalAmount = selectedItems.reduce((sum, item) => sum + item.price, 0);

          const mockExpense: Omit<Expense, 'id'> = {
            amount: totalAmount,
            category: '食費',
            description: `${storeName}での買い物`,
            date: new Date(),
            imageUrl,
            storeName,
            items: selectedItems,
          };

          // レシートから在庫品も検出
          const mockInventoryItems: Omit<InventoryItem, 'id'>[] = selectedItems.map((item) => ({
            name: item.name,
            quantity: item.quantity,
            unit: item.unit,
            category: '食品',
            imageUrl,
          }));

          resolve({
            expense: mockExpense,
            inventoryItems: mockInventoryItems,
          });
        } else {
          // 在庫品のみを検出
          const mockItems: Omit<InventoryItem, 'id'>[] = [
            {
              name: ['米', '醤油', '砂糖', '塩', '味噌'][Math.floor(Math.random() * 5)],
              quantity: Math.floor(Math.random() * 10) + 1,
              unit: ['kg', '本', 'g'][Math.floor(Math.random() * 3)],
              category: '調味料',
              imageUrl,
            },
          ];

          resolve({
            inventoryItems: mockItems,
          });
        }
      }, 1500); // 処理時間をシミュレート
    });
  };

  const captureImage = async () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0);
        const imageUrl = canvas.toDataURL('image/jpeg');
        setCapturedImage(imageUrl);

        // 画像解析を開始
        setIsProcessing(true);
        const data = await analyzeImage(imageUrl);
        setExtractedData(data);
        setIsProcessing(false);
      }
    }
  };

  const handleConfirm = () => {
    if (capturedImage) {
      onCapture(capturedImage, extractedData);
      stopCamera();
    }
  };

  const handleRetake = () => {
    setCapturedImage(null);
    setExtractedData({});
    setIsProcessing(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90">
      <div className="relative h-full w-full max-w-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 z-10 rounded-full bg-white p-2 shadow-lg transition-all hover:bg-gray-100 active:scale-95"
        >
          <X className="size-6 text-gray-800" />
        </button>

        {error ? (
          <div className="flex h-full items-center justify-center p-4">
            <div className="rounded-lg bg-white p-6 text-center">
              <p className="mb-4 text-red-600">{error}</p>
              <button
                onClick={onClose}
                className="rounded-lg bg-blue-500 px-6 py-2 text-white hover:bg-blue-600"
              >
                閉じる
              </button>
            </div>
          </div>
        ) : (
          <div className="flex h-full flex-col items-center justify-center p-4">
            {capturedImage ? (
              <div className="relative w-full">
                <img src={capturedImage} alt="Captured" className="w-full rounded-lg shadow-lg" />

                {isProcessing && (
                  <div className="absolute inset-0 flex items-center justify-center rounded-lg bg-black/50">
                    <div className="text-center text-white">
                      <Sparkles className="mx-auto mb-2 size-12 animate-pulse" />
                      <p className="font-medium">画像を解析中...</p>
                    </div>
                  </div>
                )}

                {!isProcessing && (
                  <div className="mt-4 max-h-60 overflow-y-auto rounded-lg bg-white p-4">
                    <h3 className="mb-2 font-bold text-gray-800">検出された情報:</h3>
                    {extractedData.expense && (
                      <div className="mb-3 rounded-lg bg-blue-50 p-3">
                        <p className="mb-1 text-sm font-medium text-blue-900">💰 支出</p>
                        {extractedData.expense.storeName && (
                          <p className="mb-1 text-sm font-bold text-gray-800">
                            {extractedData.expense.storeName}
                          </p>
                        )}
                        <p className="text-gray-700">
                          ¥{extractedData.expense.amount.toLocaleString()} - {extractedData.expense.category}
                        </p>
                        {extractedData.expense.items && extractedData.expense.items.length > 0 && (
                          <div className="mt-2 space-y-1">
                            {extractedData.expense.items.map((item, idx) => (
                              <p key={idx} className="text-xs text-gray-600">
                                • {item.name} - ¥{item.price} ({item.quantity}{item.unit})
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    {extractedData.inventoryItems && extractedData.inventoryItems.length > 0 && (
                      <div className="rounded-lg bg-green-50 p-3">
                        <p className="mb-2 text-sm font-medium text-green-900">📦 在庫品</p>
                        <div className="space-y-1">
                          {extractedData.inventoryItems.map((item, idx) => (
                            <p key={idx} className="text-sm text-gray-700">
                              • {item.name} - {item.quantity}{item.unit}
                            </p>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="mt-4 flex gap-4">
                  <button
                    onClick={handleRetake}
                    disabled={isProcessing}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-gray-600 px-6 py-3 font-medium text-white shadow-lg transition-all hover:bg-gray-700 disabled:opacity-50 active:scale-95"
                  >
                    <Camera className="size-5" />
                    撮り直す
                  </button>
                  <button
                    onClick={handleConfirm}
                    disabled={isProcessing}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-500 px-6 py-3 font-medium text-white shadow-lg transition-all hover:bg-blue-600 disabled:opacity-50 active:scale-95"
                  >
                    <Check className="size-5" />
                    登録する
                  </button>
                </div>
              </div>
            ) : (
              <div className="relative w-full">
                <video
                  ref={videoRef}
                  autoPlay
                  playsInline
                  className="w-full rounded-lg shadow-lg"
                />
                <canvas ref={canvasRef} className="hidden" />
                <button
                  onClick={captureImage}
                  className="mx-auto mt-4 flex items-center justify-center gap-2 rounded-full bg-gradient-to-r from-blue-500 to-green-500 p-6 font-medium text-white shadow-lg transition-all hover:from-blue-600 hover:to-green-600 active:scale-95"
                >
                  <Camera className="size-8" />
                </button>
                <p className="mt-2 text-center text-white">レシートや在庫品を撮影してください</p>
                <p className="mt-1 text-center text-sm text-gray-300">
                  自動で支出と在庫を検出します
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
