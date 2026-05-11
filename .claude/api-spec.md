# API・UI仕様

## エンドポイント

```
POST /api/upload
  - multipart/form-data で CSV ファイル受け取り
  - レスポンスは text/event-stream（SSE）
  - 処理を同期的に実行しながら進捗イベントを流す
  - 最後の done イベントに base64 エンコードした ZIP を含める
  - エラー時は error イベントを返してストリームを閉じる
```

旧来の `GET /api/progress/{job_id}` と `GET /api/download/{job_id}` は廃止。
ジョブIDによる状態管理は不要（1リクエスト＝1処理）。

## SSE イベント形式

進捗イベント（processing中）:
```
data: {"step": "kouchi", "pct": 25, "message": "高知注文データ作成中..."}
```

完了イベント（最終）:
```
data: {"step": "done", "pct": 100, "message": "完了", "filename": "260511_1430_出荷データ.zip", "data": "<base64文字列>"}
```

エラーイベント:
```
data: {"step": "error", "pct": 0, "message": "エラー内容"}
```

## プログレス ステップ

| step | pct | メッセージ |
|---|---|---|
| `parsing` | 10 | CSVを読み込み中... |
| `kouchi` | 25 | 高知注文データ作成中... |
| `sakai_main` | 40 | 堺メイン注文データ作成中... |
| `sakai_cooler` | 55 | 堺クーラー注文データ作成中... |
| `sakai_yupacket` | 65 | 堺ゆうパケット注文データ作成中... |
| `total_pick` | 75 | トータルピック表作成中... |
| `picking_list` | 90 | ピッキングリスト作成中... |
| `zipping` | 97 | ZIPにまとめています... |
| `done` | 100 | 完了（`data` フィールドに base64 ZIP を含む） |

## フロントエンド フロー

1. ユーザーがCSVを選択／ドロップ
2. `fetch POST /api/upload` を `ReadableStream` で受け取る
3. SSEイベントをパースしてプログレスバーを更新
4. `step === "done"` を受信したら:
   - `atob(event.data)` → `Uint8Array` → `Blob(type="application/zip")`
   - `URL.createObjectURL(blob)` → `<a>` を生成して `.click()` でダウンロード起動
5. `step === "error"` を受信したら赤いアラート表示

## フロントエンド UI 要件

- Tailwind CSS CDN（ビルド不要）
- 日本語UI、シンプルデザイン
- ファイルドラッグ&ドロップ対応
- SSEでプログレスバーをリアルタイム更新
- 完了後にブラウザが自動ダウンロードを起動（ボタン不要）
- エラー時は赤いアラート表示

## Vercel 設定ファイル

```json
// vercel.json
{
  "version": 2,
  "builds": [{ "src": "api/index.py", "use": "@vercel/python" }],
  "routes": [
    { "src": "/api/(.*)", "dest": "api/index.py" },
    { "src": "/(.*)", "dest": "/public/$1" }
  ]
}
```

```python
# api/index.py
from app.main import app
```

## ローカル起動手順（トラブル回避）

```powershell
# 1. 既存の python プロセスを全停止
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. pycache を削除
Get-ChildItem -Recurse -Include "*.pyc","__pycache__" | Remove-Item -Recurse -Force

# 3. 新規起動（--reload なし推奨）
$p = Start-Process -PassThru -WindowStyle Hidden python `
    -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000" `
    -WorkingDirectory "<プロジェクトルート>"
```
