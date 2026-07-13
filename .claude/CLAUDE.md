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
├── main.py               # FastAPI app & router登録、GET / で INDEX を返す
├── _html.py              # Tailwind UI を Python 文字列 INDEX として埋め込み
├── routers/upload.py     # POST /api/upload（SSEストリーミング＋base64 ZIP返却）
├── services/
│   ├── csv_parser.py     # CSV読み込み・文字コード判定・棚番分類
│   ├── kouchi_order.py   # 高知注文データ Excel生成
│   ├── sakai_order.py    # 堺メイン/クーラー/ゆうパケット Excel生成
│   ├── total_pick.py     # トータルピック表 Excel生成
│   ├── picking_list.py   # ピッキングリスト PDF生成
│   └── zip_builder.py    # 全ZIPをひとつに束ねる
└── utils/excel_helpers.py
vercel.json               # Vercel ルーティング設定
```

**静的ファイルは存在しない**。フロントHTMLは `app/_html.py` の `INDEX` 文字列として持ち、
`GET /` が `HTMLResponse` で返す。サーバーレス環境でのファイル読み込み失敗（FileNotFoundError）
を避けるため。`public/` `static/` ディレクトリを復活させないこと。

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
#   Output Directory: (空欄) ← 静的配信はしない。全リクエストが api/index.py に入る
```

## 重要な実装メモ

- **CSVの文字コード**: `utf-8-sig → cp932 → euc_jp → iso-2022-jp` の順に厳密デコードを試し、
  ヘッダーに `管理番号`・`棚番` が現れた文字コードを採用する。どれも読めなければ `ValueError`。
  - **`shift_jis` ではなく `cp932` を使うこと**。`shift_jis` codec は 髙(髙橋)・﨑(山﨑)・①・㈱・℡ などの
    NEC/IBM拡張文字を復号できず「文字化け(�)」になる。これらは実在の顧客名に頻出する。
  - **`errors="replace"` で握りつぶさないこと**。壊れた文字コードは黙って「�」や空の出力になるより、
    エラーにしてユーザーに知らせる方がよい。
- 全角マイナスは `excel_helpers.normalize_dash()` で半角 `-` に統一する（住所・電話・郵便番号）。
  「−」に見える文字は U+2212 / U+FF0D / U+2010 など複数あり、1つだけ `.replace()` しても変換漏れする。
  長音符「ー」(U+30FC) は「クーラー」等に出るため変換対象外。
- **サーバーレス設計**: DB不使用、ジョブ状態なし、ファイル書き出しなし
- `POST /api/upload` が SSE でリアルタイム進捗を流しながら同期処理し、最後の `done` イベントに base64 エンコードした ZIP を埋め込む
- フロントエンドは `done` イベントの base64 から `Blob` を生成してブラウザダウンロードを起動する
- openpyxlで「文字列強制」は `cell.number_format = '@'` + 値を `str()` でセット（`'` プレフィックス不要）
- 列アクセスは必ず `row.get("列名", "")` を使う（列が存在しない場合でも KeyError にならないように）
- 重い処理（Excel/PDF生成）は `asyncio.to_thread` でイベントループ外に逃がす。そうしないと SSE の進捗が流れない
- Vercel の関数タイムアウトは現在 全プラン **デフォルト300秒**。それでも大量CSVでは超過しうる点に注意。

## 詳細ドキュメント

@business-logic.md
@api-spec.md
