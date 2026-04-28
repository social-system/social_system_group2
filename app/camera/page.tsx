//"use client"; // クライアントコンポーネントとして定義
//
//import { useRef, useState, useCallback } from "react";
//import Webcam from "react-webcam";
//// import "./styles.css"; // もしファイルがない場合はエラーになるので一旦コメントアウト
//
//const videoConstraints = {
//  width: 720,
//  height: 360,
//  facingMode: "user",
//};
//
//export default function CameraPage() { // Next.jsのページとして使う場合は default export
//  const [isCaptureEnable, setCaptureEnable] = useState<boolean>(false);
//  const webcamRef = useRef<Webcam>(null);
//  const [url, setUrl] = useState<string | null>(null);
//
//
////
//  //const capture = useCallback(() => {
//  //  const imageSrc = webcamRef.current?.getScreenshot();
//  //  if (imageSrc) {
//  //    setUrl(imageSrc);
//  //  }
//  //}, [webcamRef]);
////
//
//  const uploadImage = async (imageSrc: string) => {
//   try {
//    // Base64 → Blob に変換
//    const res = await fetch(imageSrc);
//    const blob = await res.blob();
//  
//    const formData = new FormData();
//    formData.append(“file”, blob, “capture.jpg”);
//  
//    // APIにPOST（URLは自分のサーバーに変更）
//    const response = await fetch(“https://your-api-endpoint.com/upload”, {
//     method: “POST”,
//     body: formData
//    });
//  
//    const data = await response.json();
//    console.log(“アップロード成功:“, data);
//   } catch (error) {
//    console.error(“アップロード失敗:“, error);
//   }
//  };
//  const capture = useCallback(async () => {
//   const imageSrc = webcamRef.current?.getScreenshot();
//   if (imageSrc) {
//    setUrl(imageSrc);
//  
//    await uploadImage(imageSrc);
//   }
//  }, [webcamRef]);
//
//
//
//  return (
//    <div style={{ padding: "20px" }}>
//      <header>
//        <h1>カメラアプリ</h1>
//      </header>
//
//      {isCaptureEnable || (
//        <button onClick={() => setCaptureEnable(true)}>カメラを開始する</button>
//      )}
//
//      {isCaptureEnable && (
//        <>
//          <div>
//            <button onClick={() => setCaptureEnable(false)}>カメラを終了する</button>
//          </div>
//          <div style={{ marginTop: "10px" }}>
//            <Webcam
//              audio={false}
//              width={540}
//              height={360}
//              ref={webcamRef}
//              screenshotFormat="image/jpeg"
//              videoConstraints={videoConstraints}
//            />
//          </div>
//          <button onClick={capture} style={{ marginTop: "10px" }}>
//            キャプチャ（撮影）
//          </button>
//        </>
//      )}
//
//      {url && (
//        <div style={{ marginTop: "20px" }}>
//          <hr />
//          <h3>撮影された画像</h3>
//          <button onClick={() => setUrl(null)}>削除</button>
//          <div>
//            <img src={url} alt="Screenshot" style={{ marginTop: "10px" }} />
//          </div>
//        </div>
//      )}
//    </div>
//  );
//}


"use client";

import { useRef, useState, useCallback } from "react";
import Webcam from "react-webcam";

const videoConstraints = {
  width: 720,
  height: 360,
  facingMode: "user",
};



export default function CameraPage() {
  const [isCaptureEnable, setCaptureEnable] = useState<boolean>(false);
  const webcamRef = useRef<Webcam>(null);
  const [url, setUrl] = useState<string | null>(null);

  // --- 追加：画像をサーバーにアップロードする関数 ---
  const uploadImage = async (imageSrc: string) => {
    try {
      // Base64 (データURL) → Blob に変換
      const res = await fetch(imageSrc);
      const blob = await res.blob();

      const formData = new FormData();
      formData.append("file", blob, "capture.jpg");

      // APIにPOST（※実際のAPI URLに書き換えてください）
      //const response = await fetch("https://your-api-endpoint.com/upload", {
      //const response = await fetch("https://webhook.site/7f4126d9-cae0-4eb0-8647-3c3eaded2f37", { 
      // 修正後 (PythonサーバーのURL):
      //const response = await fetch("http://localhost:8000/upload", { 
      const response = await fetch("http://localhost:8000/receipt/items", {   
        method: "POST",
        body: formData,
      });

      if (!response.ok) throw new Error("アップロードに失敗しました");

      const data = await response.json();
      console.log("アップロード成功:", data);
    } catch (error) {
      console.error("アップロード失敗:", error);
    }
  };

  // --- 修正：キャプチャ時にアップロード関数を呼び出す ---
  const capture = useCallback(async () => {
    const imageSrc = webcamRef.current?.getScreenshot();
    if (imageSrc) {
      setUrl(imageSrc); // 画面表示用にセット
      await uploadImage(imageSrc); // サーバーへ送信
    }
  }, [webcamRef]);

  return (
    <div style={{ padding: "20px" }}>
      <h1>カメラアプリ（アップロード機能付き）</h1>
      
      {!isCaptureEnable ? (
        <button onClick={() => setCaptureEnable(true)}>カメラを開始</button>
      ) : (
        <>
          <button onClick={() => setCaptureEnable(false)}>カメラを終了</button>
          <div style={{ marginTop: "10px" }}>
            <Webcam
              audio={false}
              width={540}
              height={360}
              ref={webcamRef}
              screenshotFormat="image/jpeg"
              videoConstraints={videoConstraints}
            />
          </div>
          <button onClick={capture} style={{ marginTop: "10px", padding: "10px 20px", background: "blue", color: "white" }}>
            撮影してアップロード
          </button>
        </>
      )}

      {url && (
        <div style={{ marginTop: "20px" }}>
          <h3>最新の撮影結果:</h3>
          <img src={url} alt="Screenshot" width={300} />
        </div>
      )}
    </div>
  );
}