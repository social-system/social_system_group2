"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation"; // 自動で戻るために追加

// あなたのAPIエンドポイントURLに書き換えてください
//const API_URL = "https://your-api-endpoint.com/expenses";
//const API_URL = "https://webhook.site/7f4126d9-cae0-4eb0-8647-3c3eaded2f37";

// 修正後 (PythonサーバーのURL):
const API_URL = "http://localhost:8000/kakeibo/add";
const RECIPE_API_URL = "http://localhost:8080/api/v1/recipes/suggest";

export default function KakeiboPage() {
//  const router = useRouter();
  const [expenses, setExpenses] = useState<any[]>([]);
  
  // 入力フォームの状態管理（足りない分を補完しました）
  const [item, setItem] = useState("");
  const [num, setNum] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [ingredients, setIngredients] = useState("0"); // 0:いいえ、1:はい
  const [deleteId, setDeleteId] = useState("");


// --- 新規追加：AI提案用の状態 ---
  const [prompt, setPrompt] = useState(""); // AIへのリクエスト文
  const [isGenerating, setIsGenerating] = useState(false); // ローディング
//  const [addedCount, setAddedCount] = useState(0); // レシピ追加数カウント
  const [recipeStock, setRecipeStock] = useState<any[]>([]); // 3つのレシピを貯める配列
  const [selectedRecipe, setSelectedRecipe] = useState<any>(null); // 詳細表示用

// --- 追加：レシピ提案の結果を保存する ---
//  const [suggestedRecipe, setSuggestedRecipe] = useState<any>(null);


// 画面モード: 'input' (通常) | 'comparison' (比較) | 'detail' (詳細)
  const [viewMode, setViewMode] = useState<'input' | 'comparison' | 'detail'>('input');


  // 1. データ読み込み (Read)
  useEffect(() => {
    fetchExpenses();
  }, []);

  // --- 修正：レシピを3つ追加した段階で戻る (onClose相当) ---
{/*
  useEffect(() => {
    if (addedCount >= 3) {
      alert("レシピを3つ追加しました。一覧に戻ります。");
      router.push("/"); // または window.location.href = "/"
    }
  }, [addedCount, router]);
*/}

// 3つ溜まったら比較画面へ
  useEffect(() => {
    if (recipeStock.length === 3) {
      setViewMode('comparison');
    }
  }, [recipeStock]);

  const fetchExpenses = async () => {
    try {
      const res = await axios.get(API_URL);
      setExpenses(res.data);
    } catch (err) {
      console.error("読み込み失敗", err);
    }
  };

  // 2. データ追加 (Create)
  const handleAdd = async () => {
    try {
      await axios.post(API_URL, { 
        item, 
        num: Number(num), 
        amount: Number(amount), 
        date: Number(date), 
        ingredients: Number(ingredients)
      });
      // 入力欄をすべてリセット
      setItem(""); setNum(""); setAmount(""); setDate(""); setIngredients("0");
      fetchExpenses(); // リスト更新
    } catch (err) {
      alert("追加に失敗しました");
    }
  };

// AIにレシピをリクエスト（配列に追加するだけ）
  const handleGenerateStep = async (e: React.FormEvent) => {
    e.preventDefault();
//    if (!prompt || isGenerating) return;
    if (isGenerating) return;//空欄許可
    setIsGenerating(true);

// プロンプトが空の場合のデフォルト値を設定
    const currentPrompt = prompt || "おすすめのレシピ";    


//　　　　実際
//    try {
//      const res = await axios.post(RECIPE_API_URL, { currentPrompt });
//      setRecipeStock(prev => [...prev, res.data]); 


//以下テスト用
// API通信をシミュレート（1.5秒待機）
    await new Promise((resolve) => setTimeout(resolve, 1500));

    try {
      // テスト用のダミーレシピデータ
      const testRecipes = [
        {
          title: `${currentPrompt}のスピード炒め`,
          cookingTime: 15,
          estimatedCost: 400,
          instructions: "1. 材料を切ります。\n2. 強火で一気に炒めます。\n3. 醤油と塩胡椒で味を整えて完成です！"
        },
        {
          title: `絶品！${currentPrompt}の煮込み`,
          cookingTime: 40,
          estimatedCost: 600,
          instructions: "1. 下ごしらえをします。\n2. 出汁と一緒に弱火でじっくり煮込みます。\n3. 味が染み込んだら出来上がり。"
        },
        {
          title: `ヘルシーな${currentPrompt}サラダ`,
          cookingTime: 5,
          estimatedCost: 300,
          instructions: "1. 新鮮な状態でスライスします。\n2. 特製ドレッシングをかけます。\n3. 盛り付けて完成。"
        }
      ];

      // 現在のストック数に合わせて、3つのうち1つをランダムまたは順番に選択
      const mockData = testRecipes[recipeStock.length % testRecipes.length];

      setRecipeStock(prev => [...prev, mockData]);

//テストここまで
     
      
//      setPrompt("");
      if (recipeStock.length + 1 === 3) {
              setPrompt(""); // 3回目終了時だけ
            }
    } catch (err) {
      alert("レシピ生成に失敗しました");
    } finally {
      setIsGenerating(false);
    }
  };

  // 家計簿に最終登録する関数
  const handleFinalAdd = async (recipe: any) => {
    try {
      await axios.post(API_URL, {
        item: recipe.title || "AIレシピ",
        num: 1,
        amount: recipe.estimatedCost || 0,
        date: Number(new Date().toISOString().split('T')[0].replace(/-/g, '')),
        ingredients: 1
      });
      alert("家計簿に追加しました！");
      // 全てリセットして最初の画面へ
      setRecipeStock([]);
      setSelectedRecipe(null);
      setViewMode('input');
      fetchExpenses();
    } catch (err) {
      alert("家計簿への追加に失敗しました");
    }
  };

{/*
// --- 追加：curl -X POST ... と同じ動きをする関数 ---
  const handleSuggestRecipe = async () => {
    try {
      const res = await axios.post(RECIPE_API_URL, {}); // -d '{}' と同じ
      setSuggestedRecipe(res.data); // 結果を保存
      alert("レシピを提案しました！");
    } catch (err) {
      console.error("レシピ提案失敗", err);
      alert("レシピ提案に失敗しました。サーバーが8080ポートで動いているか確認してください。");
    }
  };

  // --- 修正：AIにレシピ提案を頼み、自動で追加する関数 ---
  const handleSuggestAndAddRecipe = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt || isGenerating) return;

    setIsGenerating(true);
    try {
      // 1. AIにレシピ提案を頼む (POSTリクエストにpromptを含める)
      const res = await axios.post(RECIPE_API_URL, { prompt }); 
      const recipeData = res.data;
      setSuggestedRecipe(recipeData);

      // 2. AIが返してきたレシピを家計簿に追加する (onAdd相当)
      // APIのレスポンス形式に合わせて適宜マッピングしてください
      await axios.post(API_URL, {
        item: recipeData.title || "AI提案レシピ", 
        num: 1,
        amount: recipeData.estimatedCost || 0, // レスポンスに金額があれば
        date: Number(new Date().toISOString().split('T')[0].replace(/-/g, '')), // 今日の日付
        ingredients: 1 // 食材なので1
      });

      // 3. カウントアップとリセット
      setAddedCount((prev) => prev + 1);
      setPrompt("");
      fetchExpenses(); // リスト更新
      alert(`「${recipeData.title}」を追加しました！`);

    } catch (err) {
      console.error("レシピ提案失敗", err);
      alert("レシピ提案または追加に失敗しました。");
    } finally {
      setIsGenerating(false);
    }
  };

*/}


  // 3. データ削除 (Delete)
  const handleDeleteById = async (id?: string) => {
    const targetId = id || deleteId;
    if (!targetId) return alert("IDを入力してください");
    
    try {
      await axios.delete(`${API_URL}/${targetId}`);
      setDeleteId("");
      fetchExpenses();
    } catch (err) {
      alert("削除に失敗しました");
    }
  };


// ========================================================
  // 画面レンダリングの切り分け
  // ========================================================

  // A. 詳細表示画面
  if (viewMode === 'detail' && selectedRecipe) {
    return (
      <div style={{ padding: '20px', maxWidth: '600px', margin: '0 auto' }}>
        <button onClick={() => setViewMode('comparison')} style={{ marginBottom: '10px' }}>← 比較画面へ戻る</button>
        <div style={{ padding: '20px', border: '2px solid #ff9800', borderRadius: '12px', backgroundColor: '#fff' }}>
          <h2 style={{ color: '#e67e22' }}>{selectedRecipe.title}</h2>
          <p><strong>⏱ 調理時間:</strong> {selectedRecipe.cookingTime || '--'} 分</p>
          <p><strong>💰 推定費用:</strong> {selectedRecipe.estimatedCost || 0} 円</p>
          <hr />
          <p><strong>作り方:</strong></p>
          <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{selectedRecipe.instructions}</div>
          
          <button 
            onClick={() => handleFinalAdd(selectedRecipe)}
            style={{ width: '100%', marginTop: '20px', backgroundColor: '#4CAF50', color: 'white', padding: '15px', border: 'none', borderRadius: '8px', fontWeight: 'bold', fontSize: '1.1rem', cursor: 'pointer' }}
          >
            このレシピに決定して家計簿に追加
          </button>
        </div>
      </div>
    );
  }

  // B. 3つのレシピ比較画面
  if (viewMode === 'comparison') {
    return (
      <div style={{ padding: '20px' }}>
        <h1 style={{ textAlign: 'center' }}>AIが3つのレシピを提案しました</h1>
        <p style={{ textAlign: 'center', color: '#666' }}>比較して、気になるレシピの詳細を確認してください。</p>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginTop: '20px' }}>
          {recipeStock.map((rcp, i) => (
            <div key={i} style={{ border: '2px solid #eee', padding: '15px', borderRadius: '12px', backgroundColor: '#fafafa', textAlign: 'center' }}>
              <h3 style={{ height: '3em' }}>{rcp.title}</h3>
              <p>⏱ {rcp.cookingTime || '--'}分 / 💰 {rcp.estimatedCost || 0}円</p>
              <button 
                onClick={() => { setSelectedRecipe(rcp); setViewMode('detail'); }}
                style={{ width: '100%', padding: '10px', backgroundColor: '#ff9800', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}
              >
                詳細を見る
              </button>
            </div>
          ))}
        </div>
        <div style={{ textAlign: 'center', marginTop: '30px' }}>
          <button onClick={() => { setRecipeStock([]); setViewMode('input'); }} style={{ color: '#999', border: 'none', background: 'none', textDecoration: 'underline', cursor: 'pointer' }}>
            やり直して入力画面に戻る
          </button>
        </div>
      </div>
    );
  }

  // C. 通常の入力画面 (初期画面)
  return (


    <div style={{ padding: '20px' }}>
      <Link href="/">← 戻る</Link>
      <h1>家計簿アプリ</h1>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxWidth: '300px' }}>
        <input value={item} onChange={(e) => setItem(e.target.value)} placeholder="品名 (例: りんご)" />
        <input type="number" value={num} onChange={(e) => setNum(e.target.value)} placeholder="個数" />
        <input type="number" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="金額" />
        <input type="number" value={date} onChange={(e) => setDate(e.target.value)} placeholder="日付 (例: 20240101)" />
        <select value={ingredients} onChange={(e) => setIngredients(e.target.value)}>
          <option value="0">食材以外</option>
          <option value="1">食材</option>
        </select>
        <button onClick={handleAdd} style={{ backgroundColor: '#4CAF50', color: 'white', padding: '10px' }}>追加する</button>
      </div>
{/* --- 追加：レシピ提案セクション --- */}
      <hr style={{ margin: '20px 0' }} />

      <section style={{ 
        padding: '20px', 
        backgroundColor: '#fffcf5', 
        borderRadius: '12px', 
        border: '2px solid #ff9800' 
      }}>
        <h2 style={{ marginTop: 0 }}>🤖 AIにレシピを相談 ({recipeStock.length} / 3)</h2>
        <form onSubmit={handleGenerateStep} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例: 冷蔵庫にある豚肉で簡単に作れるもの"
            style={{ 
              padding: '12px', 
              borderRadius: '8px', 
              border: '1px solid #ccc', 
              minHeight: '80px',
              fontSize: '16px' 
            }}
            disabled={isGenerating}
          />
          <button 
            type="submit"
            //disabled={isGenerating || !prompt}
            disabled={isGenerating}
            style={{ 
              backgroundColor: isGenerating ? '#ccc' : '#ff9800', 
              color: 'white', 
              padding: '12px', 
              borderRadius: '8px', 
              border: 'none', 
              fontWeight: 'bold',
              cursor: isGenerating ? 'not-allowed' : 'pointer'
            }}
          >
            {isGenerating ? "AIが考え中..." : `${recipeStock.length + 1}つ目のレシピを提案してもらう`}
          </button>
        </form>

        {recipeStock.length > 0 && (
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            {recipeStock.map((r, i) => <span key={i}>✅ {r.title}</span>)}
          </div>
        )}
      </section>

      <hr style={{ margin: '30px 0' }} />

      {/* 既存の履歴一覧 */}
      <h2>履歴一覧</h2>
      <ul>
        {expenses.map((ex) => (
          <li key={ex.id} style={{ marginBottom: '10px', display: 'flex', alignItems: 'center' }}>
            <span style={{ minWidth: '200px' }}>{ex.item}: {ex.amount}円 ({ex.num}個)</span>
            <button onClick={() => handleDeleteById(ex.id)} style={{ marginLeft: '10px', color: 'red' }}>削除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

{/*
      <h2>AIレシピ提案</h2>
      <button 
        onClick={handleSuggestRecipe} 
        style={{ backgroundColor: '#ff9800', color: 'white', padding: '10px', borderRadius: '5px', border: 'none', cursor: 'pointer' }}
      >
        今日のレシピを提案してもらう
      </button>

      {suggestedRecipe && (
        <div style={{ marginTop: '10px', padding: '10px', border: '1px solid #ccc', borderRadius: '5px' }}>
          <h3>提案結果:</h3>
          <pre>{JSON.stringify(suggestedRecipe, null, 2)}</pre>
        </div>
      )}
*/}


{/* --- 修正：AIレシピ提案セクション --- */}
{/*
      <section style={{ backgroundColor: '#f9f9f9', padding: '15px', borderRadius: '8px' }}>
        <h2>AIレシピ提案 ({addedCount} / 3)</h2>
        <form onSubmit={handleSuggestAndAddRecipe} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="例: 鶏肉と卵を使った、子供が喜ぶレシピを教えて"
            style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ccc', minHeight: '80px' }}
            disabled={isGenerating}
          />
*/}
{/* 
      <section style={{ 
              margin: '30px 0', 
              padding: '20px', 
              backgroundColor: '#ffffff', 
              borderRadius: '12px', 
              boxShadow: '0 4px 15px rgba(0,0,0,0.1)', // 浮き出し効果
              borderLeft: '6px solid #ff9800', // オレンジのアクセント線
              display: 'block' // 確実な表示を保証
            }}>
              <h2 style={{ 
                marginTop: 0, 
                display: 'flex', 
                alignItems: 'center', 
                gap: '10px',
                color: '#333' 
              }}>
                <span style={{ fontSize: '24px' }}>🤖</span> 
                AIレシピ提案 
                <span style={{ 
                  fontSize: '14px', 
                  backgroundColor: '#ff9800', 
                  color: 'white', 
                  padding: '2px 8px', 
                  borderRadius: '20px' 
                }}>
                  {addedCount} / 3
                </span>
              </h2>

              <form onSubmit={handleSuggestAndAddRecipe} style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
                <div style={{ position: 'relative' }}>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder="例: 鶏肉と卵を使った、子供が喜ぶレシピを教えて"
                    style={{ 
                      width: '100%', 
                      minHeight: '120px', // 少し高さを確保
                      padding: '12px', 
                      borderRadius: '8px', 
                      border: '2px solid #eee',
                      fontSize: '16px',
                      lineHeight: '1.5',
                      boxSizing: 'border-box',
                      backgroundColor: '#fafafa',
                      outline: 'none',
                      display: 'block' // 確実に表示
                    }}
                    disabled={isGenerating}
                    onFocus={(e) => e.target.style.borderColor = '#ff9800'}
                    onBlur={(e) => e.target.style.borderColor = '#eee'}
                  />
                  {!prompt && !isGenerating && (
                    <div style={{
                      position: 'absolute',
                      bottom: '10px',
                      right: '10px',
                      fontSize: '12px',
                      color: '#aaa',
                      pointerEvents: 'none'
                    }}>
                      入力してください
                    </div>
                  )}
                </div>



*/}







{/*
          <button 
            type="submit"
            disabled={isGenerating || !prompt}
            style={{ 
              backgroundColor: isGenerating ? '#ccc' : '#ff9800', 
              color: 'white', 
              padding: '12px', 
              borderRadius: '5px', 
              border: 'none', 
              cursor: isGenerating ? 'not-allowed' : 'pointer',
              fontWeight: 'bold'
            }}
          >
            {isGenerating ? "AIがレシピを考案中..." : "レシピを生成して追加"}
          </button>
        </form>

        {suggestedRecipe && (
          <div style={{ marginTop: '15px', padding: '10px', border: '1px solid #ff9800', borderRadius: '5px', backgroundColor: '#fff' }}>
            <h4 style={{ margin: '0 0 5px 0' }}>最新の提案結果:</h4>
            <p><strong>{suggestedRecipe.title}</strong></p>
            <details>
              <summary style={{ cursor: 'pointer', fontSize: '0.8rem' }}>JSON詳細を表示</summary>
              <pre style={{ fontSize: '12px', overflow: 'auto' }}>{JSON.stringify(suggestedRecipe, null, 2)}</pre>
            </details>
          </div>
        )}
      </section>



      <hr style={{ margin: '20px 0' }} />

      <h2>履歴一覧</h2>
      <ul>
        {expenses.map((ex) => (
          <li key={ex.id} style={{ marginBottom: '10px' }}>
            {ex.item}: {ex.amount}円 ({ex.num}個) 
            <button onClick={() => handleDeleteById(ex.id)} style={{ marginLeft: '10px' }}>削除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
*/}