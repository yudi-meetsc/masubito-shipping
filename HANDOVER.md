# 引き継ぎチェックリスト（HANDOVER）

> **このファイルは引き継ぎ完了後に削除してよい**（`.claude/CLAUDE.md` 冒頭の該当メモも一緒に消す）。
> 前オーナー: yudi (yudi-meetsc / p.yudi@meetsc.co.jp) → 新オーナー: j.davis (j.davis@meetsc.co.jp)

**新しくこのリポジトリを引き継いだ人へ / Claude へ:**
GitHub のコードを clone しただけでは本番運用は完結しない。GitHub 外に依存先が複数ある。
以下の未完了タスクを上から順に潰していくこと。Claude はセッション開始時にこのファイルを読み、
残タスクをユーザーに知らせ、可能なものは手伝う（現状確認コマンドは各項目に記載）。

---

## 1. GitHub リポジトリ移管の完了確認
- yudi → j.davis 個人アカウントへの**移管を申請済み**。j.davis が承諾するまで所有権は移らない。
- 承諾済みかは所有者名で確認できる:
  ```bash
  gh repo view <owner>/masubito-shipping --json owner --jq .owner.login
  ```
  `yudi-meetsc` のままなら未承諾、j.davis のユーザー名に変わっていれば完了。
- 移管が完了したら、手元の remote を張り替える:
  ```bash
  git remote set-url origin https://github.com/<新owner>/masubito-shipping.git
  ```

## 2. Vercel の再接続（本番デプロイ）
- Vercel プロジェクトは **Meets Consulting チーム（組織）に移管済み**。本番は
  https://masubito-shipping.vercel.app （`master` への push で自動デプロイ）。
- **GitHub 移管が完了すると、リポジトリのパスが変わり Vercel ↔ GitHub の連携が切れて自動デプロイが止まる。**
  - Vercel プロジェクト → Settings → Git → **新しいリポジトリに再接続**する。
  - j.davis 個人リポジトリに移す場合、**Vercel の GitHub App を j.davis のアカウント/リポジトリで承認**しないと
    組織の Vercel から見えない。
- 再接続後、`master` にテスト push して本番デプロイが緑になることを確認する。
- 環境変数は**使っていない**ので再設定不要。

## 3. Google Apps Script / Google Drive
- 移植元の GAS（出荷、および発送の `convertAndSave`）は Apps Script 上にある。
- `.gs` は**ハードコードされた Drive フォルダ ID** にファイルを保存する実装。新オーナーは
  Apps Script プロジェクトと当該 Drive フォルダの**編集権限**が必要。
- この Web アプリ（ZIP ダウンロード方式）で代替する場合は GAS の Drive 保存は使わなくてよい。

## 4. データの入手元・出力先
- 入力 CSV: CROSSMALL の注文/納品エクスポート、佐川の出荷履歴、飛脚ゆうパケットの取込明細。
- 出力 ZIP（伝票 CSV / Excel / PDF）を最終的に取り込む相手（CROSSMALL 等）。

## 5. 所有権の分割に関する注意（要判断）
- 現状の予定: **Vercel = Meets Consulting 組織**、**GitHub = j.davis 個人アカウント**、という分割になる。
  動作はするが、j.davis が抜けるとコードが個人アカウント側に残る。会社所有に統一したいなら、
  GitHub も個人ではなく **GitHub の組織（Meets）** に移管する方がよい。移管前なら向き先を変えやすい。
- 継続的にアクセスが必要な旧メンバー（yudi 等）は、移管後に**コラボレーターとして再追加**が必要。

---

## 完了したら
上記がすべて済んだら、この `HANDOVER.md` と、`.claude/CLAUDE.md` 冒頭の「新オーナーへ」メモを削除して
コミットする。以降の通常運用の情報は `README.md` と `.claude/*.md` に揃っている。
