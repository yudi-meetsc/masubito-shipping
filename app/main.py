from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.routers import upload

_INDEX_HTML = (Path(__file__).parent.parent / "public" / "index.html").read_text(encoding="utf-8")

app = FastAPI(title="ますびと商店 出荷データ作成")
app.include_router(upload.router)


@app.get("/")
async def root():
    return HTMLResponse(_INDEX_HTML)
