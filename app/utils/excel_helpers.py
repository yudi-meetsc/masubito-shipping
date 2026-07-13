from openpyxl.cell import Cell

# 全角マイナス／各種ダッシュを半角 '-' に統一する。
# 同じ「−」に見えても、CSVの文字コードと入力方法で別のコードポイントで届く:
#   CP932の 0x817C -> U+FF0D（－）、shift_jis codec では U+2212（−）、
#   Windows IME や UTF-8のCSVでは U+FF0D が最も多い。
# U+2212 だけを見ていると住所・電話・郵便番号の変換漏れが起きるため、まとめて潰す。
# ※ U+30FC（長音符「ー」）は「クーラー」など語中に出るので対象外。
_DASH_TRANS = str.maketrans({c: "-" for c in "−－‐‑‒–—―"})


def normalize_dash(value: str) -> str:
    """Collapse full-width minus / dash variants to ASCII '-'."""
    return value.translate(_DASH_TRANS)


def set_str(cell: Cell, value) -> None:
    """Write value as a forced-string cell (no auto type conversion)."""
    cell.value = str(value) if value is not None else ""
    cell.number_format = "@"
