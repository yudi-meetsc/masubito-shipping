import asyncio
import base64
import json
from datetime import datetime

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse

from app.services import csv_parser, kouchi_order, sakai_order, total_pick, picking_list, zip_builder

router = APIRouter()


def _evt(step: str, pct: int, message: str, **extra) -> str:
    payload = {"step": step, "pct": pct, "message": message, **extra}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@router.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "CSVファイルをアップロードしてください")

    content = await file.read()

    async def generate():
        try:
            ts = datetime.now().strftime("%y%m%d_%H%M")
            date_str = datetime.now().strftime("%Y年%m月%d日")

            yield _evt("parsing", 10, "CSVを読み込み中...")
            rows = await asyncio.to_thread(csv_parser.parse, content)
            classified = csv_parser.classify(rows)

            kouchi_rows = classified["kouchi"]
            sakai_24 = classified["sakai_24"]
            sakai_3 = classified["sakai_3"]
            non_kouchi = sakai_24 + sakai_3

            sub_zips: dict[str, bytes] = {}

            yield _evt("kouchi", 25, "高知注文データ作成中...")
            if kouchi_rows:
                sub_zips[f"{ts}_注文データ_高知.zip"] = await asyncio.to_thread(
                    kouchi_order.build, kouchi_rows, ts
                )

            yield _evt("sakai_main", 40, "堺メイン注文データ作成中...")
            sakai_zips = await asyncio.to_thread(sakai_order.build, sakai_24, sakai_3, ts)
            if "main" in sakai_zips:
                sub_zips[f"{ts}_注文データ_堺メイン.zip"] = sakai_zips["main"]

            yield _evt("sakai_cooler", 55, "堺クーラー注文データ作成中...")
            if "cooler" in sakai_zips:
                sub_zips[f"{ts}_注文データ_堺クーラー.zip"] = sakai_zips["cooler"]

            yield _evt("sakai_yupacket", 65, "堺ゆうパケット注文データ作成中...")
            if "yupacket" in sakai_zips:
                sub_zips[f"{ts}_注文データ_堺ゆうパケット.zip"] = sakai_zips["yupacket"]

            yield _evt("total_pick", 75, "トータルピック表作成中...")
            if non_kouchi:
                sub_zips[f"{ts}_トータルピック表.zip"] = await asyncio.to_thread(
                    total_pick.build, non_kouchi, ts
                )

            yield _evt("picking_list", 90, "ピッキングリスト作成中...")
            if sakai_24 or sakai_3:
                pl_zip = await asyncio.to_thread(
                    picking_list.build, sakai_24, sakai_3, ts, date_str
                )
                if pl_zip:
                    sub_zips[f"{ts}_ピッキングリスト.zip"] = pl_zip

            yield _evt("zipping", 97, "ZIPにまとめています...")
            master = await asyncio.to_thread(zip_builder.build, sub_zips)

            filename = f"{ts}_出荷データ.zip"
            b64 = base64.b64encode(master).decode("ascii")
            yield _evt("done", 100, "完了", filename=filename, data=b64)

        except Exception as exc:
            yield _evt("error", 0, str(exc))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
