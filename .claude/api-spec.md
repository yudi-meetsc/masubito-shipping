# API・UI仕様

## エンドポイント

```
POST /api/upload
  - multipart/form-data で CSV ファイル受け取り
  - バックグラウンドで処理開始、即座に { job_id: "xxx" } を返す

GET /api/progress/{job_id}
  - Server-Sent Events (text/event-stream)
  - data: {"step": "kouchi", "pct": 25, "message": "高知注文データ作成中..."}
  - 完了: data: {"step": "done", "pct": 100, "download_url": "/api/download/{job_id}"}
  - エラー: data: {"step": "error", "message": "エラー内容"}

GET /api/download/{job_id}
  - 全ZIPを1つのZIPにまとめてダウンロード
  - Content-Disposition: attachment; filename*=UTF-8''yyyyMMdd_HHmm_出荷データ.zip
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
| `done` | 100 | 完了 |

## フロントエンド UI

- Tailwind CSS CDN（ビルド不要）
- 日本語UI、シンプルデザイン
- ファイルドラッグ&ドロップ対応
- SSEでプログレスバーをリアルタイム更新
- 完了後にダウンロードボタン表示
- エラー時は赤いアラート表示

## サーバー起動手順（トラブル回避）

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
