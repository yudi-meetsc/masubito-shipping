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
| 進捗通知 | Server-Sent Events (SSE) |
| フロントエンド | HTML + Tailwind CSS (CDN) + Vanilla JS |

## プロジェクト構成

```
app/
├── main.py               # FastAPI app & router登録
├── routers/upload.py     # POST /api/upload, GET /api/progress/{id}, GET /api/download/{id}
├── services/
│   ├── csv_parser.py     # CSV読み込み・文字コード判定・棚番分類
│   ├── kouchi_order.py   # 高知注文データ Excel生成
│   ├── sakai_order.py    # 堺メイン/クーラー/ゆうパケット Excel生成
│   ├── total_pick.py     # トータルピック表 Excel生成
│   ├── picking_list.py   # ピッキングリスト PDF生成
│   └── zip_builder.py    # 全ZIPをひとつに束ねる
├── schemas/job.py        # JobStatus Pydanticモデル + in-memory jobs dict
└── utils/excel_helpers.py
static/index.html         # Tailwind UI
tmp/                      # 処理中ファイル一時置き場（30分後自動削除）
```

## 開発・実行

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000
# ※ --reload を使うと pycache のせいで古いコードが残ることがある。
#   再起動時は必ず pycache を削除してから起動すること。
```

## 重要な実装メモ

- CSVは Shift_JIS 優先、chardet で検出、UTF-8 fallback
- DB不使用。ジョブ状態はメモリ上の辞書（シングルプロセス前提）
- openpyxlで「文字列強制」は `cell.number_format = '@'` + 値を `str()` でセット（`'` プレフィックス不要）
- 全角マイナス「−」は半角「-」に変換してからExcelへ書き込む
- サーバー再起動時は必ず全 python プロセスを kill してから起動（古いプロセスがポート8000を保持したまま残ることがある）
- 列アクセスは必ず `row.get("列名", "")` を使う（列が存在しない場合でも KeyError にならないように）

## 詳細ドキュメント

@business-logic.md
@api-spec.md
