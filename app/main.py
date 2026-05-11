import asyncio
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import upload

app = FastAPI(title="ますびと商店 出荷データ作成")
app.include_router(upload.router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.on_event("startup")
async def startup() -> None:
    Path("tmp").mkdir(exist_ok=True)
    asyncio.create_task(_cleanup_loop())


async def _cleanup_loop() -> None:
    while True:
        await asyncio.sleep(1800)
        now = time.time()
        for f in Path("tmp").glob("*"):
            if f.is_file() and now - f.stat().st_mtime > 1800:
                f.unlink(missing_ok=True)
