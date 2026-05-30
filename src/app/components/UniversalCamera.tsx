import { useRef, useState, useEffect } from 'react';
import { Camera, X, Check, Sparkles } from 'lucide-react';
import type { InventoryItem } from '../App';


//const kakeibo_URL = "http://localhost:8000";
const kakeibo_ocr = "https://social-system-group2.onrender.com";
//const kakeibo_URL = "https://social-system-group2-3.onrender.com";
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
      // 1. 画像URLからBlob（バイナリデータ）を取得
      const res = await fetch(imageUrl);
      const blob = await res.blob();

      // 2. ★ Blobの実態（MIMEタイプ）に合わせて、適切な拡張子のファイル名を作る
      let fileName = "capture.jpg";
      if (blob.type === "image/png") fileName = "capture.png";
      if (blob.type === "image/webp") fileName = "capture.webp";

      // 3. FormDataの組み立て
      const formData = new FormData();
      formData.append("file", blob, fileName); // 仕様通りのキー名「file」

      try {
        console.log(`OCR解析リクエスト送信中... (${fileName}, タイプ: ${blob.type})`);
        
        const response = await fetch(`${kakeibo_ocr}/ocr/receipts/extract`, {
          method: "POST",
          // ※重要※ headers: { "Content-Type": "..." } は絶対に書かない（今のままで大正解）
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

  // 登録ボタンを押した時の処理（POST /receipts の入れ子構造に完全準拠）
// 登録ボタンを押した時の処理（クリーンな下書きを prepare に投げてから本登録する仕様に修正）
// 登録ボタンを押した時の処理（手動追加と同じ項目・構造に揃えて prepare に投げる）
// 登録ボタンを押した時の処理（prepareの返却値をそのまま本登録へ流す形に修正）
// 登録ボタンを押した時の処理（prepareを通してから本登録する確定版）
  const handleConfirmCall = async () => {
    if (!capturedImage) return;
    setIsProcessing(true);

    try {
      // 1. 日付を prepare が好む文字列形式「YYYY-MM-DD」にクレンジング
      let dateStr = new Date().toISOString().split('T')[0]; // 初期値は今日
      if (extractedData.purchased_at) {
        const s = String(extractedData.purchased_at).trim();
        if (s.length === 8 && !s.includes("-")) {
          dateStr = `${s.substring(0, 4)}-${s.substring(4, 6)}-${s.substring(6, 8)}`;
        } else if (s.includes("-")) {
          dateStr = s.split('T')[0];
        }
      }

      // 2. 余計な ID（product_id や category_id）を一切含まない、純粋な下書きオブジェクトを組み立てる
      const prepareBody = {
        status: "needs_confirmation",
        store_name: (extractedData.store_name || "SHOP").trim(),
        purchased_at: dateStr,
        total_amount: Number(extractedData.total_amount) || 0,
        items: Array.isArray(extractedData.items)
          ? extractedData.items.map((item: any) => ({
              raw_name: (item.raw_name || "不明な商品").trim(),
              normalized_name: (item.normalized_name || item.raw_name || "不明な商品").trim(),
              category_name: item.category_name || "食費", // 文字列のみを指定
              purchased_quantity: Number(item.purchased_quantity) || 1,
              purchased_unit: item.purchased_unit || "個",
              base_quantity: Number(item.base_quantity || item.purchased_quantity) || 1,
              base_unit: item.base_unit || item.purchased_unit || "個",
              unit_price: Number(item.unit_price) || 0,
              line_total: Number(item.line_total) || 0,
              is_inventory_target: true, // カメラからの登録は在庫連動をONにする
              confidence: 1.0,
              warnings: []
            }))
          : [],
        warnings: []
      };

      console.log("【1/2】/receipts/prepare に送信するデータ:", prepareBody);

      // 3. /receipts/prepare に送信して、バックエンドに正規オブジェクト（receipt）を組み立ててもらう
      const prepareResponse = await fetch(`${kakeibo_URL}/receipts/prepare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(prepareBody),
      });

      if (!prepareResponse.ok) {
        const prepareErrDetail = await prepareResponse.json().catch(() => ({}));
        console.error("Prepareが拒否した理由:", prepareErrDetail);
        throw new Error(`データの事前解決(prepare)に失敗しました。ステータス: ${prepareResponse.status}`);
      }
      
      const prepareData = await prepareResponse.json();
      
      // バックエンドが正常に補完・パースしてくれた本登録用のオブジェクトを取り出す
      const finalReceiptPayload = prepareData.receipt;

      if (!finalReceiptPayload) {
        throw new Error("サーバーから返ってきた receipt オブジェクトが空です。");
      }

      // 4. バックエンドが作った finalReceiptPayload のアイテムを、強制的に在庫対象(true)にする
      if (Array.isArray(finalReceiptPayload.items)) {
        finalReceiptPayload.items = finalReceiptPayload.items.map((item: any) => ({
          ...item,
          is_inventory_target: true
        }));
      }

      console.log("【2/2】/receipts（本登録）に送信する確定データ:", finalReceiptPayload);

      // 5. 完成したオブジェクトをそのまま /receipts に POST して保存
      const response = await fetch(`${kakeibo_URL}/receipts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(finalReceiptPayload),
      });

      if (!response.ok) {
        const errorDetail = await response.json().catch(() => ({}));
        console.error("レシート本登録エラー詳細:", errorDetail);
        throw new Error(`レシート確定エラー: ${response.status}`);
      }

      const resData = await response.json();
      const createdId = resData.id || resData.receipt_id || 'success';
      alert(`確定レシートと在庫を同期登録しました！ (レシートID: ${createdId})`);

      onCapture(); // App.tsx 側の最新データ再取得をトリガー
      stopCamera();
    } catch (err) {
      console.error("登録プロセス全体で失敗:", err);
      alert("データベースへの登録に失敗しました。ブラウザのコンソールログを確認してください。");
    } finally {
      setIsProcessing(false);
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
                      <p className="font-medium">データを同期処理中...</p>
                    </div>
                  </div>
                )}
                {!isProcessing && (
                  <div className="mt-4 rounded-lg bg-white p-4">
                    <h3 className="mb-2 font-bold text-gray-800">解析・プレビュー情報:</h3>
                    <div className="mb-3 rounded-lg bg-blue-50 p-3">
                      <p className="mb-1 text-sm font-medium text-blue-900">💰 店舗・金額概要</p>
                      <p className="text-gray-700">
                        {extractedData.store_name || "サンプルスーパー"} - ¥{(extractedData.total_amount || 0).toLocaleString()}
                      </p>
                    </div>
                    {extractedData.items && extractedData.items.length > 0 && (
                      <div className="rounded-lg bg-green-50 p-3">
                        <p className="mb-2 text-sm font-medium text-green-900">📦 購入アイテム明細</p>
                        <div className="space-y-1">
                          {extractedData.items.map((item, idx) => (
                            <p key={idx} className="text-sm text-gray-700">
                              • {item.normalized_name || item.raw_name} - ¥{item.line_total} ({item.purchased_quantity}{item.purchased_unit || "個"})
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