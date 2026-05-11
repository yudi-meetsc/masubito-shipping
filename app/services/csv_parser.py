import csv
import io
from typing import List, Dict, Any

import chardet


def _detect_encoding(raw: bytes) -> str:
    result = chardet.detect(raw)
    enc = (result.get("encoding") or "shift_jis").lower()
    if "utf" in enc:
        return "utf-8-sig"
    return "shift_jis"


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
    enc = _detect_encoding(content)
    try:
        text = content.decode(enc, errors="replace")
    except Exception:
        text = content.decode("utf-8", errors="replace")

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
