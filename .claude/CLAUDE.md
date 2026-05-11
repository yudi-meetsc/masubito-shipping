# ますびと商店 出荷データ作成 Web アプリ

CSVをアップロード → 複数Excel/PDFをZIPでダウンロードするWebアプリ。
Google Apps Script (`script_new.txt`) からの移植。

## 技術スタック

| レイヤー | 技術 |
|---|---|
| バックエンド | Python 3.11+, FastAPI |
| Excel生成 | openpyxl |
| PDF生成 | reportlab (CIDフォント HeiseiKakuGo-W5) |
| ZIP | Python標準 `zipfile` |
| 進捗通知 | Server-Sent Events (SSE) — アップロードと同一リクエスト内でストリーミング |
| フロントエンド | HTML + Tailwind CSS (CDN) + Vanilla JS |
| デプロイ | Vercel (サーバーレス Python) |

## プロジェクト構成

```
api/
└── index.py              # Vercel エントリーポイント（app をインポートするだけ）
app/
├── main.py               # FastAPI app & router登録
├── routers/upload.py     # POST /api/upload（SSEストリーミング＋base64 ZIP返却）
├── services/
│   ├── csv_parser.py     # CSV読み込み・文字コード判定・棚番分類
│   ├── kouchi_order.py   # 高知注文データ Excel生成
│   ├── sakai_order.py    # 堺メイン/クーラー/ゆうパケット Excel生成
│   ├── total_pick.py     # トータルピック表 Excel生成
│   ├── picking_list.py   # ピッキングリスト PDF生成
│   └── zip_builder.py    # 全ZIPをひとつに束ねる
└── utils/excel_helpers.py
public/index.html         # Tailwind UI（Vercelが静的配信）
vercel.json               # Vercel ルーティング設定
```

`schemas/job.py` と `tmp/` は削除済み。ジョブ状態管理・ファイル書き出しは不要になった。

## 開発・実行（ローカル）

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000
# ※ --reload を使うと pycache のせいで古いコードが残ることがある。
#   再起動時は必ず pycache を削除してから起動すること。
```

## デプロイ（Vercel）

```bash
# GitHub に push → Vercel が自動デプロイ
# Vercel プロジェクト設定:
#   Framework Preset: Other
#   Root Directory: (空欄)
#   Build Command: (空欄)
#   Output Directory: public
```

## 重要な実装メモ

- CSVは Shift_JIS 優先、chardet で検出、UTF-8 fallback
- **サーバーレス設計**: DB不使用、ジョブ状態なし、ファイル書き出しなし
- `POST /api/upload` が SSE でリアルタイム進捗を流しながら同期処理し、最後の `done` イベントに base64 エンコードした ZIP を埋め込む
- フロントエンドは `done` イベントの base64 から `Blob` を生成してブラウザダウンロードを起動する
- openpyxlで「文字列強制」は `cell.number_format = '@'` + 値を `str()` でセット（`'` プレフィックス不要）
- 全角マイナス「−」は半角「-」に変換してからExcelへ書き込む
- 列アクセスは必ず `row.get("列名", "")` を使う（列が存在しない場合でも KeyError にならないように）
- Vercel Hobby プランの関数タイムアウトは **60秒**。大量CSVの場合は注意。

## 詳細ドキュメント

@business-logic.md
@api-spec.md
