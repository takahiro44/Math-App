"""公開デモ用の簡易保護。

バックエンドを公開すると Gemini API キーを誰でも叩ける状態になるので、
共有パスコードとレートリミットで事故を防ぐ。**セキュリティ機構ではなく事故防止**が
目的で、完璧さは狙っていない。

どちらも環境変数が未設定なら無効になり、開発を妨げない。
"""

import logging
import os
import secrets
import threading
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

PASSCODE_HEADER = "X-App-Passcode"

# keep-alive（GitHub Actions の cron）が叩くので、認証もレートリミットも免除する。
EXEMPT_PATHS = frozenset({"/health"})


def client_ip(request: Request) -> str:
    """クライアントIPを取得する。

    Cloud Run はプロキシ経由なので request.client.host はプロキシのIPになる。
    実クライアントは X-Forwarded-For の左端に入る。
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class PasscodeAuthMiddleware(BaseHTTPMiddleware):
    """共有パスコードによる簡易認証。

    APP_PASSCODE が未設定・空なら何もしない（開発時はこの状態）。
    """

    def __init__(self, app, passcode: str | None = None):
        super().__init__(app)
        self.passcode = (passcode if passcode is not None else os.getenv("APP_PASSCODE", "")).strip()
        if self.passcode:
            logger.info("パスコード認証を有効化しました（ヘッダ: %s）", PASSCODE_HEADER)
        else:
            logger.info("APP_PASSCODE が未設定のため認証なしで動作します")

    async def dispatch(self, request: Request, call_next):
        if not self.passcode:
            return await call_next(request)

        # CORS プリフライトはカスタムヘッダを載せてこないので必ず通す。
        # ここで弾くとブラウザからのリクエストが全滅する。
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        provided = request.headers.get(PASSCODE_HEADER, "")
        # 定数時間比較（タイミング攻撃対策というより作法として）
        if not secrets.compare_digest(provided, self.passcode):
            logger.warning(
                "パスコード不一致で拒否しました ip=%s path=%s", client_ip(request), request.url.path
            )
            return JSONResponse(
                {"detail": f"{PASSCODE_HEADER} ヘッダが不正です"}, status_code=401
            )

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """IPごとの簡易レートリミット（インメモリ・スライディングウィンドウ）。

    プロセス単位なので、インスタンスが複数に増えると実効上限も倍になる。
    事故防止が目的なので許容している（docs/deploy.md に明記）。
    """

    def __init__(self, app, limit_per_minute: int | None = None, window_seconds: int = 60):
        super().__init__(app)
        if limit_per_minute is None:
            limit_per_minute = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))
        self.limit = limit_per_minute
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        # 同期エンドポイントはスレッドプールで走るので排他が必要
        self._lock = threading.Lock()
        if self.limit > 0:
            logger.info("レートリミットを有効化しました（%d req/%d秒/IP）", self.limit, self.window)
        else:
            logger.info("RATE_LIMIT_PER_MINUTE=0 のためレートリミットは無効です")

    def _check(self, ip: str) -> tuple[bool, int]:
        """(許可するか, Retry-After秒) を返す。"""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[ip]
            # ウィンドウから外れた履歴を捨てる
            while hits and now - hits[0] >= self.window:
                hits.popleft()

            if len(hits) >= self.limit:
                retry_after = max(1, int(self.window - (now - hits[0])) + 1)
                return False, retry_after

            hits.append(now)

            # 空になったIPを残し続けるとメモリが単調増加するので掃除する
            if len(self._hits) > 10_000:
                for stale_ip in [k for k, v in self._hits.items() if not v]:
                    del self._hits[stale_ip]

            return True, 0

    async def dispatch(self, request: Request, call_next):
        if self.limit <= 0 or request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        # プリフライトは実処理を伴わないので数えない
        if request.method == "OPTIONS":
            return await call_next(request)

        ip = client_ip(request)
        allowed, retry_after = self._check(ip)
        if not allowed:
            logger.warning("レートリミット超過 ip=%s path=%s", ip, request.url.path)
            return JSONResponse(
                {"detail": f"リクエストが多すぎます。{retry_after}秒後に再試行してください。"},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
