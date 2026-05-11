import io
import math
import zipfile
from collections import defaultdict, OrderedDict
from typing import List, Dict, Any, Tuple

from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))
FONT = "HeiseiKakuGo-W5"

PAGE_W, PAGE_H = A4          # 595.28 x 841.89 pt
MARGIN = 18.0                # 0.25 inch ≈ 18 pt
NUM_COLS = 33                # columns A(1) through AG(33)
COL_W = (PAGE_W - 2 * MARGIN) / NUM_COLS
ROW_H = 21.0                 # 21pt per row (matches GAS rowHeight)


def _col_x(n: int) -> float:
    """Left x of 1-indexed column (A=1, B=2, …, AG=33)."""
    return MARGIN + (n - 1) * COL_W


def _row_bottom(n: int) -> float:
    """Bottom y of 1-indexed row in reportlab coordinates (origin at bottom)."""
    return PAGE_H - MARGIN - n * ROW_H


def _text_y(n: int) -> float:
    return _row_bottom(n) + 5


# Right edge of AG = left edge of col 34 = PAGE_W - MARGIN
_RIGHT_EDGE = _col_x(34)
# Content width from B to AG (32 columns)
_CONTENT_W = _RIGHT_EDGE - _col_x(2)

_GREY_FILL = HexColor("#F2F2F2")
_WHITE_FILL = HexColor("#FFFFFF")
_HEADER_FILL = HexColor("#D0D0D0")


def _group_rows(sakai_24: List[Dict[str, Any]], sakai_3: List[Dict[str, Any]]):
    """Yield (page_key, rows) for each picking list page."""
    # shelf 2/4: group by 管理番号, one page per group
    groups: "OrderedDict[str, List[Dict[str, Any]]]" = OrderedDict()
    for row in sakai_24:
        key = row.get("管理番号", "")
        groups.setdefault(key, []).append(row)
    for mgmt, rows in groups.items():
        yield mgmt, rows

    # shelf 3: each CSV row is its own page with a unique key 管理番号_3-N
    counters: Dict[str, int] = defaultdict(int)
    for row in sakai_3:
        mgmt = row.get("管理番号", "")
        counters[mgmt] += 1
        yield f"{mgmt}_3-{counters[mgmt]}", [row]


def _get_products(rows: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """Return list of (display_name, quantity) — one entry per CSV row, no aggregation."""
    products = []
    for row in rows:
        name = row.get("標準商品名", "")
        qty_str = row.get("数量", "")
        if not name or not qty_str:
            continue
        jan = row.get("JANコード", "")
        code = row.get("商品コード", "")
        product_code = jan if jan else code
        attr1 = row.get("属性１名", "")
        attr2 = row.get("属性２名", "")
        display = f"{product_code} {name} {attr1} {attr2}".rstrip()
        qty = int(qty_str) if qty_str.isdigit() else 0
        products.append((display, qty))
    return products


def _draw_page(
    cv: canvas.Canvas,
    rows: List[Dict[str, Any]],
    date_str: str,
) -> None:
    first = rows[0]
    mgmt_num = first.get("管理番号", "").zfill(8)
    name = first.get("届け先氏名", "")
    postal = first.get("届け先郵便番号", "")
    tel = first.get("届け先ＴＥＬ", "")  # already normalized by csv_parser

    products = _get_products(rows)

    bx = _col_x(2)

    # Row 2: 管理番号 (B2) and date (AA2=col27)
    cv.setFont(FONT, 9)
    cv.drawString(_col_x(2) + 2, _text_y(2), f"管理番号：{mgmt_num}")
    cv.drawString(_col_x(27), _text_y(2), f"日付：{date_str}")
    # Underline B2:AG2
    cv.line(bx, _row_bottom(2), _RIGHT_EDGE, _row_bottom(2))

    # Rows 4-8: お届け先名ブロック (border box)
    box4_y = _row_bottom(8)
    box4_h = _row_bottom(3) - _row_bottom(8)
    cv.rect(bx, box4_y, _CONTENT_W, box4_h)
    cv.setFont(FONT, 9)
    cv.drawString(_col_x(2) + 2, _text_y(4), "お届け先名")
    cv.setFont(FONT, 14)
    cv.drawString(_col_x(3), _text_y(6), f"{name} 様")

    # Rows 10-17: お届け先情報ブロック (border box)
    box10_y = _row_bottom(17)
    box10_h = _row_bottom(9) - _row_bottom(17)
    cv.rect(bx, box10_y, _CONTENT_W, box10_h)
    cv.setFont(FONT, 9)
    cv.drawString(_col_x(2) + 2, _text_y(10), "お届け先情報")
    cv.setFont(FONT, 10)
    cv.drawString(_col_x(3), _text_y(12), str(postal))
    cv.drawString(_col_x(3), _text_y(16), str(tel))

    # Row 19: column header bar
    cv.setFillColor(_HEADER_FILL)
    cv.rect(bx, _row_bottom(19), _CONTENT_W, ROW_H, fill=1, stroke=1)
    cv.setFillColor(black)
    cv.setFont(FONT, 9)
    cv.drawString(_col_x(2) + 2, _text_y(19), "商品名")
    cv.drawString(_col_x(30), _text_y(19), "数量")  # AD = col30

    # Rows 20+: product rows (no aggregation — each CSV row = one line)
    total_qty = 0
    for i, (prod_name, qty) in enumerate(products):
        rn = 20 + i
        bg = _WHITE_FILL if i % 2 == 0 else _GREY_FILL
        cv.setFillColor(bg)
        cv.rect(bx, _row_bottom(rn), _CONTENT_W, ROW_H, fill=1, stroke=1)
        cv.setFillColor(black)
        cv.setFont(FONT, 8)
        cv.drawString(_col_x(2) + 2, _text_y(rn), prod_name)
        cv.drawString(_col_x(30), _text_y(rn), str(qty))
        total_qty += qty

    # Total row with one gap row (matches GAS: totalRow = endRow + 2)
    if products:
        tr = 20 + len(products) + 1
        cv.setFont(FONT, 9)
        cv.setFillColor(black)
        cv.rect(bx, _row_bottom(tr), _CONTENT_W, ROW_H, fill=0, stroke=1)
        cv.drawString(_col_x(2) + 2, _text_y(tr), "計")
        cv.drawString(_col_x(30), _text_y(tr), str(total_qty))

    cv.showPage()


def build(
    sakai_24: List[Dict[str, Any]],
    sakai_3: List[Dict[str, Any]],
    ts: str,
    date_str: str,
) -> bytes:
    """Return ZIP bytes containing the picking list PDF(s). date_str e.g. '2026年05月10日'."""
    pages = list(_group_rows(sakai_24, sakai_3))
    if not pages:
        return b""

    MAX_PER_PDF = 100
    num_pdfs = math.ceil(len(pages) / MAX_PER_PDF)

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for pdf_idx in range(num_pdfs):
            chunk = pages[pdf_idx * MAX_PER_PDF: (pdf_idx + 1) * MAX_PER_PDF]
            pdf_buf = io.BytesIO()
            cv = canvas.Canvas(pdf_buf, pagesize=A4)
            for _, rows in chunk:
                _draw_page(cv, rows, date_str)
            cv.save()
            suffix = f"_{pdf_idx + 1}" if num_pdfs > 1 else ""
            zf.writestr(f"{ts}_ピッキングリスト{suffix}.pdf", pdf_buf.getvalue())

    return zip_buf.getvalue()
