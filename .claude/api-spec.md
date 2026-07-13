# API・UI仕様

## エンドポイント

```
POST /api/upload/shukka
  - multipart/form-data で CSV ファイル受け取り
  - レスポンスは text/event-stream（SSE）
  - 処理を同期的に実行しながら進捗イベントを流す
  - 最後の done イベントに base64 エンコードした ZIP を含める
  - エラー時は error イベントを返してストリームを閉じる

POST /api/upload/hasso
  - multipart/form-data で最大3つのCSVを受け取る（すべて任意・最低1つ必須）
      nouhin : 納品データ_YYYYMMDD_HHMM.csv
      sagawa : shukka_rireki_YYYYMMDD*.csv（出荷履歴・佐川）
      hikkyu : 飛脚ゆうパケット便ラベル発行システム_取込明細_*.csv
  - 0件なら 400。レスポンスは出荷と同じ SSE
  - done イベントに filename / data(base64 ZIP) に加えて results（ファイル名と件数）を含む
```

旧来の `GET /api/progress/{job_id}` と `GET /api/download/{job_id}` は廃止。
ジョブIDによる状態管理は不要（1リクエスト＝1処理）。
`POST /api/upload` は `/api/upload/shukka` にリネーム済み（発送と並べるため）。

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

## プログレス ステップ（出荷）

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

## プログレス ステップ（発送）

| step | pct | メッセージ |
|---|---|---|
| `parsing` | 15 | CSVを読み込み中... |
| `yamato` | 40 | ヤマト伝票データ作成中... |
| `sagawa` | 60 | 佐川伝票データ作成中... |
| `hikkyu` | 80 | 飛脚ゆうパケット伝票データ作成中... |
| `zipping` | 95 | ZIPにまとめています... |
| `done` | 100 | 完了（`data` に base64 ZIP、`results` にファイル名と件数） |

## フロントエンド フロー

1. ユーザーがCSVを選択／ドロップ（発送は最大3ファイル選択後に「変換」ボタン）
2. `fetch POST /api/upload/{shukka,hasso}` を `ReadableStream` で受け取る
3. SSEイベントをパースしてプログレスバーを更新
4. `step === "done"` を受信したら:
   - `atob(event.data)` → `Uint8Array` → `Blob(type="application/zip")`
   - `URL.createObjectURL(blob)` → `<a>` を生成して `.click()` でダウンロード起動
5. `step === "error"` を受信したら赤いアラート表示

## フロントエンド UI 要件

- Tailwind CSS CDN（ビルド不要）
- 日本語UI、シンプルデザイン
- **上部に「出荷 / 発送」タブ**。タブごとに入力欄を差し替え、進捗バー・ダウンロード・エラー欄は共通で使い回す
  - モードごとの `endpoint` と進捗ステップ表は JS の `MODES` オブジェクトに定義する
  - 発送を実装する時は `MODES.hasso` の `endpoint` / `steps` と `#panel-hasso` の中身を埋める
  - 処理中はタブを無効化（`setBusy()`）。タブ切替時は `reset()` で共通欄をクリア
- ファイルドラッグ&ドロップ対応
- SSEでプログレスバーをリアルタイム更新
- 完了後にブラウザが自動ダウンロードを起動（ボタン不要）
- エラー時は赤いアラート表示

HTMLは `app/_html.py` の `INDEX` 文字列。静的ファイルとしては配信していない
（`GET /` が FastAPI から `HTMLResponse` で返す）。UIを直す時はこのファイルを編集する。

## Vercel 設定ファイル

全リクエスト（`/` も含む）を Python 関数に流す。静的配信はしない。

```json
// vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "50mb" }
    }
  ],
  "routes": [
    { "src": "/(.*)", "dest": "api/index.py" }
  ]
}
```

```python
# api/index.py
# app パッケージを import できるようリポジトリルートを sys.path に追加してから読み込む
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
