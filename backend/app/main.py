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
from app.middleware import PasscodeAuthMiddleware, RateLimitMiddleware  # noqa: E402
from app.routers import question, grading, print as print_router  # noqa: E402

app = FastAPI()

# 本番ドメインと localhost は完全一致で許可する。
allowed_origins = [
    o.strip()
    for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:4173"
    ).split(",")
    if o.strip()
]
# Vercel はプレビューデプロイごとに動的なドメインを発行するので、完全一致では足りない。
# 正規表現は環境変数で渡す（デフォルトなし。誤って広く開けないため）。
allowed_origin_regex = os.getenv("ALLOWED_ORIGIN_REGEX") or None

# --- ミドルウェアの順序について ---
# Starlette は「最後に add_middleware したものが最も外側」になる。
# CORS を最外側にしないと、401/429 のエラーレスポンスに CORS ヘッダが付かず、
# ブラウザ側では原因不明の「CORS エラー」としか見えなくなる。
# したがって認証・レートリミットを先に追加し、CORS を最後に追加する。
app.add_middleware(PasscodeAuthMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allowed_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)
logger.info(
    "CORS 設定: allow_origins=%s allow_origin_regex=%s",
    allowed_origins,
    allowed_origin_regex,
)

app.include_router(question.router, prefix="/question", tags=["question"])
app.include_router(grading.router, prefix="/grading", tags=["grading"])
app.include_router(print_router.router, prefix="/print", tags=["print"])

@app.get("/health")
def health():
    return {"status": "ok"}
