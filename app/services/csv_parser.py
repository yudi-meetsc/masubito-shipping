import csv
import io
from typing import List, Dict, Any, Sequence

import chardet


# 日本語CSVで実際に来る文字コード候補。順番に意味がある:
#   - utf-8-sig を最初に（UTF-8は自己検証性が高く、BOM有無どちらも扱える）
#   - shift_jis ではなく cp932 を使う。cp932 は shift_jis の上位互換で、
#     髙(髙橋)・﨑(山﨑)・①・㈱・℡・Ⅲ などのNEC/IBM拡張文字を含む。
#     これらは実在する顧客名・住所に頻出するが shift_jis では復号できず「�」になる。
_CANDIDATE_ENCODINGS = ("utf-8-sig", "cp932", "euc_jp", "iso-2022-jp")

# ヘッダーがこの列を含んでいれば、その文字コードで正しく復号できたと判断する。
# （EUC-JPのバイト列は cp932 でも「復号成功」してしまうため、
#   例外の有無だけでは判定できない。列名が読めるかどうかで見分ける。）
_REQUIRED_COLUMNS = ("管理番号", "棚番")


def _header_columns(text: str) -> List[str]:
    first_line = text.split("\n", 1)[0]
    return next(csv.reader(io.StringIO(first_line)), [])


def decode(raw: bytes, required_columns: Sequence[str], label: str = "CSV") -> str:
    """必要な列名がヘッダーに現れる文字コードを採用して復号する。"""
    for enc in _CANDIDATE_ENCODINGS:
        try:
            text = raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
        if all(c in _header_columns(text) for c in required_columns):
            return text

    detected = (chardet.detect(raw).get("encoding") or "?").lower()
    raise ValueError(
        f"{label}を読み取れませんでした。列名 {'・'.join(required_columns)} が見つかりません。"
        f"ファイルの種類が違うか、対応していない文字コードです（推定: {detected}）。"
        "Shift_JIS(CP932) または UTF-8 で保存し直してください。"
    )


def _normalize_phone(phone: str) -> str:
    phone = phone.strip()
    if phone.startswith("+81"):
        rest = phone[3:].lstrip("-").lstrip()
        return "0" + rest
    return phone


def _pad_mgmt(v: str) -> str:
    v = v.strip()
    return v.zfill(8) if v.isdigit() else v


def _pad_time_code(v: str) -> str:
    v = v.strip()
    return v.zfill(2) if v.isdigit() else v


def _pick_product_key(row: Dict[str, Any]) -> str:
    jan = str(row.get("JANコード", "")).strip()
    return jan if jan else str(row.get("商品コード", "")).strip()


def parse(content: bytes) -> List[Dict[str, Any]]:
    text = decode(content, _REQUIRED_COLUMNS, "出荷CSV")

    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        raise ValueError("CSVが空です")

    result = []
    for raw in rows:
        row = {k: (v or "").strip() for k, v in raw.items()}
        row["管理番号"] = _pad_mgmt(row.get("管理番号", ""))
        row["配送時間帯コード"] = _pad_time_code(row.get("配送時間帯コード", ""))
        row["届け先ＴＥＬ"] = _normalize_phone(row.get("届け先ＴＥＬ", ""))
        row["_product_key"] = _pick_product_key(row)

        shelf = row.get("棚番", "").strip()
        # normalise shelf 4 grouping key after we record the raw value
        row["_shelf"] = shelf
        result.append(row)

    return result


def classify(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Split rows by destination."""
    kouchi: List[Dict[str, Any]] = []
    sakai_24: List[Dict[str, Any]] = []
    sakai_3: List[Dict[str, Any]] = []

    for row in rows:
        s = row["_shelf"]
        if s == "1":
            kouchi.append(row)
        elif s in ("2", "4"):
            sakai_24.append(row)
        elif s == "3":
            sakai_3.append(row)

    return {"kouchi": kouchi, "sakai_24": sakai_24, "sakai_3": sakai_3}
