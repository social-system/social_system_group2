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

  // OCR/画像認識関数 (API 仕様書のマッピングロジックに修正)
  const analyzeImageCall = async (imageUrl: string): Promise<ExtractedData> => {
    try {
      const res = await fetch(imageUrl);
      const blob = await res.blob();
      const formData = new FormData();
      
      formData.append("upload_file", blob, "capture.jpg");

      try {
        //const response = await fetch("http://localhost:8000/ocr/receipts/extract", {
        const response = await fetch("https://social-system-group2.onrender.com/ocr/receipts/extract", {

          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          console.error("--- サーバー解析エラー発生 (ステータス: " + response.status + ") ---");
          return getMockData(imageUrl, "サーバー出力エラー時のモックデータ");
        }

        const data = await response.json();
        const apiItems = data.items || [];

        const totalAmount = apiItems.reduce((sum: number, item: any) => {
          return sum + (Number(item.price) || 0) * (Number(item.quantity) || 1);
        }, 0);

        const expense = apiItems.length > 0 ? {
          amount: totalAmount,
          category: "レシートデータ",
          description: data.store_name || "店舗名未設定",
          date: new Date(),
        } : undefined;

        const inventoryItems = apiItems.map((item: any) => ({
          name: item.name,
          quantity: Number(item.quantity) || 1,
          unit: "個",
          category: "食材",
        }));

        return {
          expense,
          inventoryItems,
        };

      } catch (networkError) {
        console.error("--- サーバー未起動または通信不能を検知 ---");
        return getMockData(imageUrl, "サーバー起動エラー時のモックデータ");
      }

    } catch (err) {
      console.error("解析失敗:", err);
      return {};
    }
  };

  const getMockData = (imageUrl: string, description: string): ExtractedData => ({
    expense: {
      amount: 1280,
      category: 'レシートデータ',
      description: 'サンプルスーパー',
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

        setIsProcessing(true);
        const data = await analyzeImageCall(imageUrl);
        setExtractedData(data);
        setIsProcessing(false);
      }
    }
  };

  // 登録ボタンを押した時の処理（POST /receipts の入れ子構造に完全準拠）
  const handleConfirmCall = async () => {
    if (!capturedImage) return;

    try {
      // YYYYMMDD形式の数値
      const todayDate = Number(new Date().toISOString().split('T')[0].replace(/-/g, ''));

      // 1. トップレベルの基本情報設定（OCRから店舗名や金額があれば使う、なければデフォルト値）
      const totalAmount = extractedData.expense ? Number(extractedData.expense.amount) : 0;
      const storeName = extractedData.expense ? extractedData.expense.description : "カメラ登録店舗";

      // 2. 入れ子にする明細アイテム (items) 配列の構築
      const itemsPayload = [];

      if (extractedData.inventoryItems && extractedData.inventoryItems.length > 0) {
        // 在庫品が検出されている場合は明細として詰め込む
        extractedData.inventoryItems.forEach((item) => {
          itemsPayload.push({
            raw_name: item.name || "不明な商品",
            normalized_name: item.name || "不明な商品",
            product_id: 1,
            category_id: 1,
            purchased_quantity: Number(item.quantity) || 1,
            purchased_unit: item.unit || "個",
            base_quantity: Number(item.quantity) || 1,
            base_unit: item.unit || "個",
            unit_price: 0, 
            line_total: 0,
            is_inventory_target: true // 食材・在庫品なので自動で在庫ロットへ反映
          });
        });
      } else {
        // 在庫品は無いが金額だけがある（一般的なレシート）場合のフォールバック明細
        itemsPayload.push({
          raw_name: "レシート一括品目",
          normalized_name: "レシート一括品目",
          product_id: 1,
          category_id: 1,
          purchased_quantity: 1,
          purchased_unit: "点",
          base_quantity: 1,
          base_unit: "点",
          unit_price: totalAmount,
          line_total: totalAmount,
          is_inventory_target: false // 通常の一般経費
        });
      }

      // 仕様書の POST /receipts リクエストボディの組み立て
      const requestBody = {
        purchased_at: todayDate,
        store_name: storeName,
        total_amount: totalAmount,
        items: itemsPayload
      };

      // 3. バックエンドへ確定データを1つのリクエストとして送信
      const response = await fetch("http://localhost:8000/receipts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`サーバーエラー: ${response.status}`);
      }

      const resData = await response.json();
      alert(`確定レシートを登録しました！ (レシートID: ${resData.id})`);
      
      // 親コンポーネントへ引き渡し、カメラコンポーネントを終了
      onCapture(capturedImage, extractedData);
      stopCamera();

    } catch (err) {
      console.error("確定レシートの登録に失敗しました:", err);
      alert("データベースへの登録に失敗しました。サーバーの接続状況を確認してください。");
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
                        <p className="mb-1 text-sm font-medium text-blue-900">💰 支出概要</p>
                        <p className="text-gray-700">
                          ¥{extractedData.expense.amount.toLocaleString()} - {extractedData.expense.description}
                        </p>
                      </div>
                    )}
                    {extractedData.inventoryItems && extractedData.inventoryItems.length > 0 && (
                      <div className="rounded-lg bg-green-50 p-3">
                        <p className="mb-2 text-sm font-medium text-green-900">📦 内訳（明細アイテム）</p>
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
                    onClick={handleConfirmCall}
                    disabled={isProcessing}
                    className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-blue-500 px-6 py-3 font-medium text-white shadow-lg transition-all hover:bg-blue-600 disabled:opacity-50 active:scale-95"
                  >
                    <Check className="size-5" />
                    確定して登録
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
                <p className="mt-2 text-center text-white">レシートや食材を撮影してください</p>
                <p className="mt-1 text-center text-sm text-gray-300">
                  確定データのみを共通データベースに登録します
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}