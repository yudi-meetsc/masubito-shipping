from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import upload

_PUBLIC = Path(__file__).parent.parent / "public"

app = FastAPI(title="ますびと商店 出荷データ作成")
app.include_router(upload.router)
app.mount("/", StaticFiles(directory=str(_PUBLIC), html=True), name="static")
