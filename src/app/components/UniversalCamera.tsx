import { useRef, useState, useEffect } from 'react';
import { Camera, X, Check, Sparkles } from 'lucide-react';
import type { Expense, InventoryItem } from '../App';
import axios from 'axios'; // axios をインポート

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

  // 撮り直すボタンなどで capturedImage が null に戻った時に、
  // 再び video 要素にストリームをセットする
  useEffect(() => {
    if (!capturedImage && stream && videoRef.current) {
      videoRef.current.srcObject = stream;
    }
  }, [capturedImage, stream]);

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
          const mockExpense: Omit<Expense, 'id'> = {
            amount: Math.floor(Math.random() * 5000) + 500,
            category: ['食費', '日用品', '交通費'][Math.floor(Math.random() * 3)],
            description: 'カメラで撮影した支出',
            date: new Date(),
            imageUrl,
          };

          // レシートから在庫品も検出
          const mockItems: Omit<InventoryItem, 'id'>[] = [
            {
              name: ['牛乳', '卵', 'パン', 'トマト', 'キャベツ'][Math.floor(Math.random() * 5)],
              quantity: Math.floor(Math.random() * 5) + 1,
              unit: ['個', 'パック', '本'][Math.floor(Math.random() * 3)],
              category: '食品',
              imageUrl,
            },
            {
              name: ['玉ねぎ', 'にんじん', 'じゃがいも', '豆腐'][Math.floor(Math.random() * 4)],
              quantity: Math.floor(Math.random() * 3) + 1,
              unit: ['個', 'パック'][Math.floor(Math.random() * 2)],
              category: '食品',
              imageUrl,
            },
          ];

          resolve({
            expense: mockExpense,
            inventoryItems: mockItems,
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

// analyzeImage関数（ロジック部分）のみを実機能に書き換え
const analyzeImageCall = async (imageUrl: string): Promise<ExtractedData> => {
  try {
    const res = await fetch(imageUrl);
    const blob = await res.blob();
    const formData = new FormData();
    formData.append("file", blob, "capture.jpg");

    try {
      // 1. 通信を試みる
      const response = await fetch("http://localhost:8000/receipt/items", {
        method: "POST",
        body: formData,
      });

      // 2. サーバーは応答したが、エラー（404, 500等）の場合
      if (!response.ok) {
        console.error("--- サーバー解析エラー発生 (ステータス: " + response.status + ") ---");
        return getMockData(imageUrl, "サーバー出力エラー時のモックデータ");
      }

      // 3. 正常な場合：JSONを解析して返す
      const data = await response.json();
      return {
        expense: data.expense || undefined,
        inventoryItems: data.items || [],
      };

    } catch (networkError) {
      // 4. そもそもサーバーが起動していない（接続拒否）場合
      console.error("--- サーバー未起動または通信不能を検知 ---");
      console.warn("検証のため、仮のデータを返却して続行します。");
      return getMockData(imageUrl, "サーバー起動エラー時のモックデータ");
    }

  } catch (err) {
    console.error("解析失敗:", err);
    return {};
  }
};

// ヘルパー関数：同じようなモックデータを何度も書かなくて済むように分離
const getMockData = (imageUrl: string, description: string): ExtractedData => ({
  expense: {
    amount: 1280,
    category: '食費（仮）',
    description: description,
    date: new Date(),
    imageUrl,
  },
  inventoryItems: [
    { name: 'デバッグ用牛乳', quantity: 1, unit: '本', category: '食品', imageUrl },
    { name: 'デバッグ用卵', quantity: 10, unit: '個', category: '食品', imageUrl },
  ],
});

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
        //const data = await analyzeImage(imageUrl);
        const data = await analyzeImageCall(imageUrl);
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

// 登録ボタンを押した時の処理（全データ一括送信版）
  const handleConfirmCall = async () => {
    if (capturedImage) {
      try {
        // 送信タスク（Promise）を溜める配列
        const sendTasks: Promise<Response>[] = [];
        
        // 当日の日付（数値型: YYYYMMDD）
        const todayDate = Number(new Date().toISOString().split('T')[0].replace(/-/g, ''));

        // ==========================================
        // 1. 支出データ（expense）があれば送信タスクに追加
        // ==========================================
        if (extractedData.expense) {
          const expenseTask = fetch("http://localhost:8000/kakeibo/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              item: extractedData.expense.category || "レシート合計",
              num: 1,
              amount: Number(extractedData.expense.amount) || 0,
              date: todayDate,
              ingredients: 0 // 支出（食材以外）
            }),
          });
          sendTasks.push(expenseTask);
        }

        // ==========================================
        // 2. 在庫データ（inventoryItems）があればすべて送信タスクに追加
        // ==========================================
        if (extractedData.inventoryItems && extractedData.inventoryItems.length > 0) {
          extractedData.inventoryItems.forEach((item) => {
            const inventoryTask = fetch("http://localhost:8000/kakeibo/add", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                item: item.name || "在庫品",
                num: Number(item.quantity) || 1,
                amount: 0, // 在庫単体の金額は不明なため0
                date: todayDate,
                ingredients: 1 // 在庫（食材）
              }),
            });
            sendTasks.push(inventoryTask);
          });
        }

        // 送るべきデータが何もなかった場合
        if (sendTasks.length === 0) {
          alert("検出されたデータがありません。");
          return;
        }

        // ==========================================
        // 3. すべての送信処理を並列で実行
        // ==========================================
        const responses = await Promise.all(sendTasks);

        // どこかでエラーが発生していないかチェック
        const hasError = responses.some(res => !res.ok);
        if (hasError) {
          throw new Error("一部のデータの登録に失敗しました。");
        }

        alert(`家計簿に合計 ${sendTasks.length} 件のデータを追加しました！`);
        
        // 親コンポーネントへの通知とカメラの停止
        onCapture(capturedImage, extractedData);
        stopCamera();
      } catch (err) {
        console.error("家計簿への追加失敗:", err);
        alert("家計簿への追加に失敗しました");
      }
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
                  <div className="mt-4 rounded-lg bg-white p-4">
                    <h3 className="mb-2 font-bold text-gray-800">検出された情報:</h3>
                    {extractedData.expense && (
                      <div className="mb-3 rounded-lg bg-blue-50 p-3">
                        <p className="mb-1 text-sm font-medium text-blue-900">💰 支出</p>
                        <p className="text-gray-700">
                          ¥{extractedData.expense.amount.toLocaleString()} - {extractedData.expense.category}
                        </p>
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
                    //onClick={handleConfirm}
                    onClick={handleConfirmCall}
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
