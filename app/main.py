from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app._html import INDEX
from app.routers import hasso, upload

app = FastAPI(title="ますびと商店 データ作成")
app.include_router(upload.router)
app.include_router(hasso.router)


@app.get("/")
async def root():
    return HTMLResponse(INDEX)
