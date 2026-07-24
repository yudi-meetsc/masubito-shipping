# ますびと商店 データ作成 Web アプリ

CSV をアップロードすると、変換結果を ZIP でダウンロードできる社内向け Web アプリ。
UI は「**出荷**」「**発送**」の 2 タブ構成。元は Google Apps Script のツールで、それを FastAPI に移植したもの。

**本番:** https://masubito-shipping.vercel.app （`master` への push で Vercel が自動デプロイ）

---

## 何をするアプリか

### 出荷タブ
CROSSMALL の注文 CSV を 1 枚アップロード → **棚番**で高知／堺に振り分け、以下を ZIP 出力する。

- 高知・堺メイン・堺クーラー・堺ゆうパケットの**注文データ**（Excel）
- **トータルピック表**（Excel）
- **ピッキングリスト**（PDF）

### 発送タブ
配送 CSV を最大 3 枚（すべて任意・最低 1 枚）アップロード → キャリア別の**注文伝票 csv 連携**を ZIP 出力する。

| 入力 | 出力 |
|---|---|
| 納品データ | ヤマト（`配送キャリア` = Y/YL）・佐川（`配送キャリア` = S） |
| 出荷履歴（佐川） | 佐川（全行） |
| 飛脚ゆうパケット取込明細 | 飛脚ゆうパケット（全行） |

処理は **Server-Sent Events (SSE)** で進捗を流しながら同期実行し、完了時に base64 エンコードした ZIP を
返す。フロントはそれを Blob 化してブラウザダウンロードを起動する。DB・ジョブ状態・サーバー側ファイル
書き出しは**一切ない**（サーバーレス設計）。

---

## 技術スタック

| レイヤー | 技術 |
|---|---|
| バックエンド | Python 3.11+ / FastAPI |
| Excel 生成 | openpyxl |
| PDF 生成 | reportlab（CID フォント HeiseiKakuGo-W5） |
| 進捗通知 | Server-Sent Events (SSE) |
| フロントエンド | HTML + Tailwind CSS (CDN) + Vanilla JS（ビルド不要） |
| デプロイ | Vercel（サーバーレス Python） |

---

## ローカルで動かす

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# → http://localhost:8000
```

> `--reload` を使うと `__pycache__` のせいで古いコードが残ることがある。
> 挙動が変だと思ったら `__pycache__` を消してから再起動する。

---

## プロジェクト構成

```
api/index.py              Vercel エントリーポイント（app.main:app を読み込むだけ）
app/
├── main.py               FastAPI app、ルーター登録、GET / で INDEX(HTML) を返す
├── _html.py              フロント UI 全体（Python 文字列 INDEX として埋め込み）
├── routers/
│   ├── upload.py         POST /api/upload/shukka（出荷）
│   └── hasso.py          POST /api/upload/hasso（発送）
├── services/
│   ├── csv_parser.py     CSV 読み込み・文字コード判定・棚番分類
│   ├── kouchi_order.py   高知 注文データ Excel
│   ├── sakai_order.py    堺メイン/クーラー/ゆうパケット Excel
│   ├── total_pick.py     トータルピック表 Excel
│   ├── picking_list.py   ピッキングリスト PDF
│   ├── hasso.py          発送データ（ヤマト/佐川/飛脚）CSV
│   └── zip_builder.py    複数ファイルを 1 つの ZIP に束ねる（出荷/発送で共用）
└── utils/
    ├── excel_helpers.py
    └── sse.py            SSE イベント整形（両ルーターで共用）
vercel.json               Vercel ルーティング設定
```

**静的ファイルは置かない。** フロント HTML は `app/_html.py` の `INDEX` 文字列として持ち、
`GET /` が返す。サーバーレス環境でのファイル読み込み失敗を避けるため。`public/` `static/` を復活させないこと。

### 詳しい仕様
UI を直したり変換ロジックをいじる前に、必ず以下を読むこと。実装の背景と「なぜこうなっているか」が書いてある。

- [`.claude/business-logic.md`](.claude/business-logic.md) — 棚番の振り分けルール、列マッピング、発送の生成条件など**業務ロジックの全仕様**
- [`.claude/api-spec.md`](.claude/api-spec.md) — エンドポイント・SSE イベント形式・プログレスステップ
- [`.claude/CLAUDE.md`](.claude/CLAUDE.md) — 実装上の注意点まとめ

---

## デプロイ（Vercel）

`master` に push すると Vercel が自動で本番デプロイする。Vercel プロジェクト設定:

- Framework Preset: **Other**
- Root Directory: （空欄）
- Build Command / Output Directory: （空欄）← 静的配信はしない。全リクエストが `api/index.py` に入る

環境変数は**使っていない**（`.env` 不要）。Vercel の関数タイムアウトはデフォルト 300 秒。
大量 CSV の出荷処理では超過しうる点に注意。

---

## ⚠️ 引き継ぎ時の注意（GitHub 以外の依存先）

このリポジトリだけでは完結しない。以下のアクセス権も一緒に引き継ぐこと。

1. **Vercel プロジェクト** — 本番デプロイ先。GitHub リポジトリと連携している。リポジトリの所有者が
   変わると連携が切れるので、Vercel 側で新リポジトリに**再接続**（または Vercel プロジェクトごと移管）する。
2. **Google Apps Script / Google Drive** — 移植元の GAS（出荷・発送 `convertAndSave`）は Apps Script 上にある。
   `.gs` は**ハードコードされた Drive フォルダ ID** に保存する実装になっている。新オーナーは Apps Script
   プロジェクトと当該 Drive フォルダの編集権限が必要。GAS 側の保存先を使わない場合はこの Web アプリで代替できる。
3. **入力 CSV の入手元** — CROSSMALL の注文/納品エクスポート、佐川の出荷履歴、飛脚ゆうパケットの取込明細。
4. **出力 ZIP の利用先** — 生成した伝票 CSV / Excel / PDF を最終的に取り込む相手（CROSSMALL 等）。

---

## 実装上の落とし穴（触る前に読む）

- **文字コードは `cp932` を使う。`shift_jis` は使わない。** `shift_jis` codec は 髙・﨑・①・㈱・℡ などの
  NEC/IBM 拡張文字を復号できず「文字化け（�）」になる。これらは実在の顧客名・住所に頻出する。
  `csv_parser.decode()` は `utf-8-sig → cp932 → euc_jp → iso-2022-jp` の順に試し、**期待する列名が読めた
  文字コードを採用する**（例外の有無だけでは判定できないため）。
- **エラーは握りつぶさない。** 壊れた文字コードを `errors="replace"` で黙って「�」にするより、エラーにして
  ユーザーに知らせる。
- **発送は GAS の挙動をそのまま再現している。** 佐川の重複排除なし・0 件でもヘッダーだけの CSV を生成・
  管理番号が空の行もそのまま出力、など。これらは「バグ」ではなく仕様。勝手に「改善」しないこと
  （変える場合は業務側と合意の上で）。
- 列アクセスは必ず `row.get("列名", "")`。列が無くても `KeyError` にしない。
- 重い処理（Excel/PDF 生成）は `asyncio.to_thread` でイベントループの外に逃がす。でないと SSE の進捗が流れない。
