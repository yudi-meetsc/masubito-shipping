"""発送データ（注文伝票csv連携）生成。

Google Apps Script (convertAndSave) からの移植。入力は最大3種のCSV（すべて任意、
最低1つ必要）。キャリアごとに 管理番号 と 伝票番号 を突き合わせた3列CSVを出力する。

GAS は Drive に個別保存していたが、ここでは ZIP にまとめてブラウザに返す。
"""

import csv
import io
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from app.services.csv_parser import decode

JST = timezone(timedelta(hours=9))

# 文字コード判定に使う列。GAS はファイル名で UTF-8/SJIS を決め打ちしていたが、
# ファイル名が変わると文字化けするため、ヘッダーが読めた文字コードを採用する。
NOUHIN_COLUMNS = ("配送キャリア", "注文管理番号", "トラッキングナンバー")
SAGAWA_COLUMNS = ("お客様管理番号", "お問い合せ送り状No.")
HIKKYU_COLUMNS = ("管理番号", "お問い合わせ番号")

YAMATO_HEADERS = ("お客様管理番号", "伝票番号", "配送便")
SAGAWA_HEADERS = ("管理番号", "お問合せ番号", "配送便")
HIKKYU_HEADERS = ("管理番号", "お問合せ番号", "配送便")


def _parse(raw: bytes, required: Sequence[str], label: str) -> List[Dict[str, Any]]:
    text = decode(raw, required, label)
    rows = []
    for row in csv.DictReader(io.StringIO(text)):
        cleaned = {(k or "").strip(): (v or "").strip() for k, v in row.items()}
        if any(cleaned.values()):  # 空行スキップ
            rows.append(cleaned)
    return rows


def parse_nouhin(raw: bytes) -> List[Dict[str, Any]]:
    return _parse(raw, NOUHIN_COLUMNS, "納品データ")


def parse_sagawa(raw: bytes) -> List[Dict[str, Any]]:
    return _parse(raw, SAGAWA_COLUMNS, "出荷履歴（佐川）")


def parse_hikkyu(raw: bytes) -> List[Dict[str, Any]]:
    return _parse(raw, HIKKYU_COLUMNS, "飛脚ゆうパケット取込明細")


def _to_csv(headers: Sequence[str], rows: List[Dict[str, str]]) -> bytes:
    """BOM付きUTF-8・CRLF（Excelで文字化けしない）。GAS の buildCsv と同じ。"""
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(headers), lineterminator="\r\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def date_prefix(filename: str) -> str:
    """ファイル名の8桁数字から yyMMdd を作る（20260710 → 260710）。無ければ今日。"""
    m = re.search(r"\d{8}", filename)
    if m:
        return m.group(0)[2:]
    return datetime.now(JST).strftime("%y%m%d")


def build_yamato(nouhin: List[Dict[str, Any]]) -> Tuple[bytes, int]:
    rows = [
        {
            "お客様管理番号": r.get("注文管理番号", ""),
            "伝票番号": r.get("トラッキングナンバー", ""),
            "配送便": "ヤマト",
        }
        for r in nouhin
        if r.get("配送キャリア") in ("Y", "YL")
    ]
    return _to_csv(YAMATO_HEADERS, rows), len(rows)


def build_sagawa(
    sagawa: Optional[List[Dict[str, Any]]],
    nouhin: Optional[List[Dict[str, Any]]],
) -> Tuple[bytes, int]:
    """出荷履歴の全行 ＋ 納品データの 配送キャリア=S の行を連結する（GAS通り重複排除なし）。"""
    rows = [
        {
            "管理番号": r.get("お客様管理番号", ""),
            "お問合せ番号": r.get("お問い合せ送り状No.", ""),
            "配送便": "佐川",
        }
        for r in (sagawa or [])
    ]
    rows += [
        {
            "管理番号": r.get("注文管理番号", ""),
            "お問合せ番号": r.get("トラッキングナンバー", ""),
            "配送便": "佐川",
        }
        for r in (nouhin or [])
        if r.get("配送キャリア") == "S"
    ]
    return _to_csv(SAGAWA_HEADERS, rows), len(rows)


def build_hikkyu(hikkyu: List[Dict[str, Any]]) -> Tuple[bytes, int]:
    rows = [
        {
            "管理番号": r.get("管理番号", ""),
            "お問合せ番号": r.get("お問い合わせ番号", ""),
            "配送便": "ゆうパケット",
        }
        for r in hikkyu
    ]
    return _to_csv(HIKKYU_HEADERS, rows), len(rows)
