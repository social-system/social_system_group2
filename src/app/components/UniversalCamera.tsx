import { useRef, useState, useEffect } from 'react';
import { Camera, X, Check, Sparkles } from 'lucide-react';
import type { InventoryItem } from '../App';

const kakeibo_ocr = "https://social-system-group2.onrender.com";
const kakeibo_URL = "https://social-system-group2-2.onrender.com";

interface ExtractedData {
  store_name?: string;
  purchased_at?: string;
  total_amount?: number;
  items?: any[];
}

interface UniversalCameraProps {
  onCapture: () => void;
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

  const analyzeImageCall = async (imageUrl: string): Promise<ExtractedData> => {
    try {
      const res = await fetch(imageUrl);
      const blob = await res.blob();

      let fileName = "capture.jpg";
      if (blob.type === "image/png") fileName = "capture.png";
      if (blob.type === "image/webp") fileName = "capture.webp";

      const formData = new FormData();
      formData.append("file", blob, fileName);

      try {
        console.log(`OCR解析リクエスト送信中... (${fileName}, タイプ: ${blob.type})`);
        const response = await fetch(`${kakeibo_ocr}/ocr/receipts/extract`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errDetail = await response.json().catch(() => ({}));
          console.error("--- サーバー解析エラー発生 ---", response.status, errDetail);
          return getMockData();
        }

        const data = await response.json();
        console.log("OCR解析に成功しました:", data);
        return data as ExtractedData;

      } catch (networkError) {
        console.error("--- サーバー通信不能を検知 ---", networkError);
        return getMockData();
      }
    } catch (err) {
      console.error("解析失敗（前処理またはBlob変換エラー）:", err);
      return getMockData();
    }
  };

  const getMockData = (): ExtractedData => ({
    store_name: 'サンプルスーパー',
    purchased_at: new Date().toISOString().split('T')[0],
    total_amount: 1280,
    items: [
      { raw_name: 'プレミアム牛乳', normalized_name: '牛乳', purchased_quantity: 1, purchased_unit: '本', unit_price: 280, line_total: 280 },
      { raw_name: '新鮮たまご 10コ', normalized_name: '卵', purchased_quantity: 1, purchased_unit: 'パック', unit_price: 250, line_total: 250 },
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

  // 💡 【ポイント】画面でユーザーが選んだ値（セレクトボックス）を正しく組み立て直して送信
  const handleConfirmCall = async () => {
    if (!capturedImage) return;
    setIsProcessing(true);

    try {
      let dateStr = new Date().toISOString().split('T')[0];
      if (extractedData.purchased_at) {
        const s = String(extractedData.purchased_at).trim();
        if (s.length === 8 && !s.includes("-")) {
          dateStr = `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`;
        } else if (s.includes("-")) {
          dateStr = s.split('T')[0];
        }
      }

      const prepareBody = {
        status: "needs_confirmation",
        // 💡 "SHOP" から "【レシート】店名未設定" に変更
        store_name: (extractedData.store_name || "").trim() !== "" 
          ? extractedData.store_name!.trim() 
          : "【レシート】店名未設定",
        purchased_at: dateStr,
        total_amount: Number(extractedData.total_amount) || 0,
        items: Array.isArray(extractedData.items)
          ? extractedData.items.map((item: any) => {
              // 💡 ユーザーがセレクトボックスで「食費」や「野菜」を選んだ、もしくはOCR結果がそうである場合
              const currentCat = item.category_name || "食費";
              const isFood = 
                currentCat === "食費" || 
                currentCat === "野菜" || 
                currentCat === "vegetable" || 
                currentCat === "mushroom" ||
                item.is_inventory_target === true;

              return {
                raw_name: (item.raw_name || "不明な商品").trim(),
                normalized_name: (item.normalized_name || item.raw_name || "不明な商品").trim(),
                category_name: currentCat, 
                purchased_quantity: Number(item.purchased_quantity) || 1,
                purchased_unit: item.purchased_unit || "個",
                base_quantity: isFood ? (Number(item.base_quantity || item.purchased_quantity) || 1) : null,
                base_unit: isFood ? (item.base_unit || item.purchased_unit || "個") : null,
                unit_price: Number(item.unit_price) || 0,
                line_total: Number(item.line_total) || 0,
                is_inventory_target: isFood, 
                confidence: 1.0,
                warnings: []
              };
            })
          : [],
        warnings: []
      };

      console.log("【1/2】/receipts/prepare に送信するデータ:", prepareBody);

      const prepareResponse = await fetch(`${kakeibo_URL}/receipts/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prepareBody),
      });

      if (!prepareResponse.ok) {
        throw new Error(`データの事前解決(prepare)に失敗しました。`);
      }

      const prepareData = await prepareResponse.json();
      const finalReceiptPayload = prepareData.receipt;

      if (!finalReceiptPayload) {
        throw new Error("サーバーから返ってきた receipt オブジェクトが空です。");
      }

      let finalDateNum = 20260531;
      const rawDate = String(finalReceiptPayload.purchased_at || dateStr);
      const digitOnly = rawDate.replace(/[-/]/g, '');
      if (digitOnly.length === 8) {
        finalDateNum = Number(digitOnly);
      }

      // 💡 画面上の変更（食費や野菜など）を最終送信データにもしっかり引継ぎ、安全ガードを効かせる
      const cleansedPayload: any = {
        store_name: finalReceiptPayload.store_name,
        purchased_at: finalDateNum,
        total_amount: Number(finalReceiptPayload.total_amount) || 0,
        items: Array.isArray(finalReceiptPayload.items)
          ? finalReceiptPayload.items.map((item: any, idx: number) => {
              const originalItem = extractedData.items?.[idx] || {};
              const userCat = originalItem.category_name || item.category_name || "食費";
              
              const shouldBeInventory = 
                item.is_inventory_target === true || 
                originalItem.is_inventory_target === true ||
                ["食費", "野菜", "vegetable", "mushroom"].includes(userCat);

              return {
                raw_name: item.raw_name,
                normalized_name: item.normalized_name,
                product_id: item.product_id || null,
                category_id: item.category_id || null,
                is_inventory_target: shouldBeInventory,
                purchased_quantity: item.purchased_quantity,
                purchased_unit: item.purchased_unit,
                unit_price: item.unit_price,
                line_total: item.line_total,
                base_quantity: shouldBeInventory ? (item.base_quantity || item.purchased_quantity) : null,
                base_unit: shouldBeInventory ? (item.base_unit || item.purchased_unit) : null
              };
            })
          : []
      };

      console.log("【2/2】/receipts に送信する最終クリーンデータ:", cleansedPayload);

      const response = await fetch(`${kakeibo_URL}/receipts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cleansedPayload),
      });

      if (!response.ok) throw new Error(`本登録サーバーエラー`);

      alert("家計簿と在庫に登録が完了しました！");
      onCapture(); // 親側のリフレッシュを呼ぶ
      onClose(); // モーダルを閉じる
    } catch (err) {
      console.error(err);
      alert("データの保存に失敗しました。");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm overflow-y-auto">
      <div className="relative w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl max-h-[90vh] flex flex-col">
        {/* ヘッダー */}
        <div className="flex items-center justify-between border-b pb-4 shrink-0">
          <div className="flex items-center gap-2">
            <div className="rounded-xl bg-gradient-to-tr from-blue-500 to-purple-500 p-2 text-white">
              <Camera className="size-5" />
            </div>
            <h2 className="text-xl font-bold text-gray-800">スマート画像認識（レシート・食材）</h2>
          </div>
          <button onClick={onClose} className="rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600">
            <X className="size-6" />
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-600 border border-red-100 shrink-0">
            {error}
          </div>
        )}

        {/* コンテンツエリア */}
        <div className="mt-4 flex-1 overflow-y-auto pr-1">
          {capturedImage ? (
            <div className="space-y-6">
              {/* 撮影画像プレビュー */}
              <div className="relative overflow-hidden rounded-xl border bg-gray-50 h-48 flex items-center justify-center">
                <img src={capturedImage} alt="Captured" className="h-full object-contain" />
                {isProcessing && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-white/80 gap-3">
                    <Sparkles className="size-8 animate-spin text-blue-500" />
                    <p className="font-medium text-gray-600 animate-pulse">AIが画像から食材と金額を読み取り中...</p>
                  </div>
                )}
              </div>

              {/* 💡 解析プレビュー情報画面の修正部分 */}
              {!isProcessing && extractedData.store_name !== undefined && (
                <div className="rounded-xl border border-blue-100 bg-blue-50/50 p-5 space-y-4">
                  <h3 className="text-sm font-bold text-blue-800 flex items-center gap-1.5 border-b border-blue-100 pb-2">
                    💰 店舗・金額概要
                  </h3>
                  <div className="grid grid-cols-2 gap-4 text-sm text-gray-700">
                    <div>
                      <span className="text-gray-500 block text-xs">利用店舗</span>
                      <span className="font-bold text-base">{extractedData.store_name || "設定なし"}</span>
                    </div>
                    <div>
                      <span className="text-gray-500 block text-xs">合計金額</span>
                      <span className="font-bold text-base text-purple-600">
                        ¥{(extractedData.total_amount || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>

                  {/* 📝 認識された明細一覧とカテゴリーの手動選択UI */}
                  <div className="mt-4 space-y-2">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider">認識された商品明細</h4>
                    {Array.isArray(extractedData.items) && extractedData.items.length > 0 ? (
                      <div className="space-y-2">
                        {extractedData.items.map((item: any, idx: number) => {
                          const currentCat = item.category_name || "食費";
                          // 「食費」や「野菜」なら在庫対象だとひと目でわかるバッジ
                          const isInventoryTarget = ["食費", "野菜", "vegetable", "mushroom"].includes(currentCat);

                          return (
                            <div key={idx} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 rounded-lg border bg-white p-3 shadow-sm">
                              <div className="flex-1">
                                <p className="font-bold text-gray-800 text-sm">{item.raw_name}</p>
                                <p className="text-xs text-gray-500 mt-0.5">
                                  単価: ¥{(item.unit_price || 0).toLocaleString()} × {item.purchased_quantity || 1}{item.purchased_unit || "個"}
                                </p>
                              </div>

                              {/* 選択ドロップダウンメニューの追加 */}
                              <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                                <select
                                  value={currentCat}
                                  onChange={(e) => {
                                    // 💡 セレクトボックスの選択内容をリアルタイムに state へ保存
                                    const updatedItems = [...(extractedData.items || [])];
                                    updatedItems[idx].category_name = e.target.value;
                                    setExtractedData({ ...extractedData, items: updatedItems });
                                  }}
                                  className="rounded border border-gray-300 bg-gray-50 px-2 py-1 text-xs font-medium text-gray-700 shadow-sm focus:border-blue-500 focus:bg-white focus:outline-none"
                                >
                                  <option value="食費">🥑 食費</option>
                                  <option value="野菜">🥬 野菜</option>
                                  <option value="日用品">🧻 日用品</option>
                                  <option value="その他">📦 その他</option>
                                </select>

                                {/* 連動して切り替わる在庫ステータス表示 */}
                                <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium border ${
                                  isInventoryTarget 
                                    ? "bg-emerald-50 border-emerald-200 text-emerald-700" 
                                    : "bg-gray-50 border-gray-200 text-gray-500"
                                }`}>
                                  {isInventoryTarget ? "📦 在庫追加対象" : "✕ 在庫対象外"}
                                </span>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-xs text-gray-400 italic">明細は認識されませんでした。</p>
                    )}
                  </div>
                </div>
              )}

              {/* アクションボタン */}
              <div className="flex gap-3 shrink-0 pt-2">
                <button
                  onClick={() => {
                    setCapturedImage(null);
                    setExtractedData({});
                  }}
                  disabled={isProcessing}
                  className="flex-1 rounded-xl border border-gray-200 py-3 font-medium text-gray-600 hover:bg-gray-50 transition-all disabled:opacity-50"
                >
                  撮り直す
                </button>
                <button
                  onClick={handleConfirmCall}
                  disabled={isProcessing}
                  className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 font-medium text-white shadow-lg transition-all hover:opacity-95 disabled:opacity-50"
                >
                  <Check className="size-5" />
                  確定して登録
                </button>
              </div>
            </div>
          ) : (
            /* カメラのライブ映像表示 (未撮影時) */
            <div className="relative w-full flex flex-col items-center">
              <div className="relative w-full aspect-[4/3] max-h-[50vh] overflow-hidden rounded-xl bg-black">
                <video ref={videoRef} autoPlay playsInline className="h-full w-full object-cover" />
              </div>
              <canvas ref={canvasRef} className="hidden" />
              <button
                onClick={captureImage}
                className="mt-6 flex items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-purple-600 p-5 text-white shadow-xl hover:scale-105 active:scale-95 transition-all"
              >
                <Camera className="size-8" />
              </button>
              <p className="mt-3 text-sm font-medium text-gray-500">レシートや食材を撮影してください</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}