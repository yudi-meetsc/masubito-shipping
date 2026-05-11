import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse, FileResponse

from app.schemas.job import JobStatus, jobs
from app.services import csv_parser, kouchi_order, sakai_order, total_pick, picking_list, zip_builder

router = APIRouter()

TMP = Path("tmp")


def _update(job_id: str, **kwargs) -> None:
    current = jobs[job_id]
    jobs[job_id] = JobStatus(**{**current.model_dump(), **kwargs})


def _process(job_id: str, content: bytes) -> None:
    try:
        ts = datetime.now().strftime("%y%m%d_%H%M")
        date_str = datetime.now().strftime("%Y年%m月%d日")

        _update(job_id, step="parsing", pct=10, message="CSVを読み込み中...")
        rows = csv_parser.parse(content)
        classified = csv_parser.classify(rows)

        kouchi_rows = classified["kouchi"]
        sakai_24 = classified["sakai_24"]
        sakai_3 = classified["sakai_3"]
        non_kouchi = sakai_24 + sakai_3

        sub_zips: dict[str, bytes] = {}

        _update(job_id, step="kouchi", pct=25, message="高知注文データ作成中...")
        if kouchi_rows:
            sub_zips[f"{ts}_注文データ_高知.zip"] = kouchi_order.build(kouchi_rows, ts)

        _update(job_id, step="sakai_main", pct=40, message="堺メイン注文データ作成中...")
        sakai_zips = sakai_order.build(sakai_24, sakai_3, ts)
        if "main" in sakai_zips:
            sub_zips[f"{ts}_注文データ_堺メイン.zip"] = sakai_zips["main"]

        _update(job_id, step="sakai_cooler", pct=55, message="堺クーラー注文データ作成中...")
        if "cooler" in sakai_zips:
            sub_zips[f"{ts}_注文データ_堺クーラー.zip"] = sakai_zips["cooler"]

        _update(job_id, step="sakai_yupacket", pct=65, message="堺ゆうパケット注文データ作成中...")
        if "yupacket" in sakai_zips:
            sub_zips[f"{ts}_注文データ_堺ゆうパケット.zip"] = sakai_zips["yupacket"]

        _update(job_id, step="total_pick", pct=75, message="トータルピック表作成中...")
        if non_kouchi:
            sub_zips[f"{ts}_トータルピック表.zip"] = total_pick.build(non_kouchi, ts)

        _update(job_id, step="picking_list", pct=90, message="ピッキングリスト作成中...")
        if sakai_24 or sakai_3:
            pl_zip = picking_list.build(sakai_24, sakai_3, ts, date_str)
            if pl_zip:
                sub_zips[f"{ts}_ピッキングリスト.zip"] = pl_zip

        _update(job_id, step="zipping", pct=97, message="ZIPにまとめています...")
        master = zip_builder.build(sub_zips)

        out_path = TMP / f"{job_id}_output.zip"
        out_path.write_bytes(master)

        _update(
            job_id,
            step="done",
            pct=100,
            message="完了",
            download_url=f"/api/download/{job_id}",
        )

    except Exception as exc:
        _update(job_id, step="error", pct=0, message=str(exc), error=str(exc))


@router.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(400, "CSVファイルをアップロードしてください")

    content = await file.read()
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus()

    asyncio.create_task(asyncio.to_thread(_process, job_id, content))
    return {"job_id": job_id}


@router.get("/api/progress/{job_id}")
async def progress(job_id: str):
    async def stream():
        while True:
            status = jobs.get(job_id)
            if status is None:
                payload = json.dumps({"step": "error", "message": "ジョブが見つかりません"})
                yield f"data: {payload}\n\n"
                break
            yield f"data: {status.model_dump_json()}\n\n"
            if status.step in ("done", "error"):
                break
            await asyncio.sleep(0.4)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/download/{job_id}")
async def download(job_id: str):
    status = jobs.get(job_id)
    if not status or status.step != "done":
        raise HTTPException(404, "ジョブが完了していません")

    out_path = TMP / f"{job_id}_output.zip"
    if not out_path.exists():
        raise HTTPException(404, "出力ファイルが見つかりません")

    filename = f"{datetime.now().strftime('%y%m%d_%H%M')}_出荷データ.zip"
    encoded = quote(filename)
    return FileResponse(
        out_path,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
