import asyncio
import base64
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app.services import hasso, zip_builder
from app.utils.sse import event as _evt

router = APIRouter()


@router.post("/api/upload/hasso")
async def upload_hasso(
    nouhin: Optional[UploadFile] = File(None),
    sagawa: Optional[UploadFile] = File(None),
    hikkyu: Optional[UploadFile] = File(None),
):
    provided = [
        (f, n)
        for f, n in (
            (nouhin, "納品データ"),
            (sagawa, "出荷履歴（佐川）"),
            (hikkyu, "飛脚ゆうパケット取込明細"),
        )
        if f and f.filename
    ]
    if not provided:
        raise HTTPException(400, "CSVファイルを1つ以上選択してください")
    for f, label in provided:
        if not f.filename.lower().endswith(".csv"):
            raise HTTPException(400, f"{label}: CSVファイルを選択してください")

    nouhin_raw = await nouhin.read() if nouhin and nouhin.filename else None
    sagawa_raw = await sagawa.read() if sagawa and sagawa.filename else None
    hikkyu_raw = await hikkyu.read() if hikkyu and hikkyu.filename else None

    # 日付プレフィックスは 納品 → 佐川 → 飛脚 の順で最初に選択されたファイル名から取る
    first_filename = provided[0][0].filename

    async def generate():
        try:
            prefix = hasso.date_prefix(first_filename)
            files: dict[str, bytes] = {}
            results: list[dict] = []

            yield _evt("parsing", 15, "CSVを読み込み中...")
            nouhin_rows = (
                await asyncio.to_thread(hasso.parse_nouhin, nouhin_raw)
                if nouhin_raw
                else None
            )
            sagawa_rows = (
                await asyncio.to_thread(hasso.parse_sagawa, sagawa_raw)
                if sagawa_raw
                else None
            )
            hikkyu_rows = (
                await asyncio.to_thread(hasso.parse_hikkyu, hikkyu_raw)
                if hikkyu_raw
                else None
            )

            yield _evt("yamato", 40, "ヤマト伝票データ作成中...")
            if nouhin_rows is not None:
                data, count = hasso.build_yamato(nouhin_rows)
                name = f"{prefix}_ヤマト_注文伝票csv連携.csv"
                files[name] = data
                results.append({"name": name, "count": count})

            yield _evt("sagawa", 60, "佐川伝票データ作成中...")
            if sagawa_rows is not None or nouhin_rows is not None:
                data, count = hasso.build_sagawa(sagawa_rows, nouhin_rows)
                name = f"{prefix}_佐川_注文伝票csv連携.csv"
                files[name] = data
                results.append({"name": name, "count": count})

            yield _evt("hikkyu", 80, "飛脚ゆうパケット伝票データ作成中...")
            if hikkyu_rows is not None:
                data, count = hasso.build_hikkyu(hikkyu_rows)
                name = f"{prefix}_飛脚ゆうパケット_注文伝票csv連携.csv"
                files[name] = data
                results.append({"name": name, "count": count})

            yield _evt("zipping", 95, "ZIPにまとめています...")
            master = await asyncio.to_thread(zip_builder.build, files)

            filename = f"{prefix}_発送データ.zip"
            b64 = base64.b64encode(master).decode("ascii")
            yield _evt(
                "done", 100, "完了", filename=filename, data=b64, results=results
            )

        except Exception as exc:
            yield _evt("error", 0, str(exc))

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
