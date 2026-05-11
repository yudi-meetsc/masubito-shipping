from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import upload

app = FastAPI(title="ますびと商店 出荷データ作成")
app.include_router(upload.router)
app.mount("/", StaticFiles(directory="public", html=True), name="static")
