"use client";

import { useState, useEffect } from "react";
import axios from "axios";
import Link from "next/link";

// あなたのAPIエンドポイントURLに書き換えてください
//const API_URL = "https://your-api-endpoint.com/expenses";
//const API_URL = "https://webhook.site/7f4126d9-cae0-4eb0-8647-3c3eaded2f37";

// 修正後 (PythonサーバーのURL):
const API_URL = "http://localhost:8000/kakeibo/add";
const RECIPE_API_URL = "http://localhost:8080/api/v1/recipes/suggest";

export default function KakeiboPage() {
  const [expenses, setExpenses] = useState<any[]>([]);
  
  // 入力フォームの状態管理（足りない分を補完しました）
  const [item, setItem] = useState("");
  const [num, setNum] = useState("");
  const [amount, setAmount] = useState("");
  const [date, setDate] = useState("");
  const [ingredients, setIngredients] = useState("0"); // 0:いいえ、1:はい
  const [deleteId, setDeleteId] = useState("");
// --- 追加：レシピ提案の結果を保存する ---
  const [suggestedRecipe, setSuggestedRecipe] = useState<any>(null);

  // 1. データ読み込み (Read)
  useEffect(() => {
    fetchExpenses();
  }, []);

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