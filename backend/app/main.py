import logging
import os
import sys

# uvicorn は root logger を設定しないので、app.* のログが stdout に出るよう自分で設定する。
# これがないと retriever の [RAG] ログ（検索結果の目視確認用）やインデックス読み込み
# 失敗の error ログが消える。retriever はモジュールロード時にインデックスを読むので、
# ルータの import より前に設定しておく必要がある。
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    stream=sys.stdout,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from app.routers import question, grading, print as print_router  # noqa: E402

app = FastAPI()

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(question.router, prefix="/question", tags=["question"])
app.include_router(grading.router, prefix="/grading", tags=["grading"])
app.include_router(print_router.router, prefix="/print", tags=["print"])

@app.get("/health")
def health():
    return {"status": "ok"}