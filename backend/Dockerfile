FROM python:3.11.9-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_PYTHON_PREFERENCE=only-system
ENV UV_LINK_MODE=copy
# ログをバッファせず即座に stdout へ流す（Cloud Run のログに遅延なく載せるため）
ENV PYTHONUNBUFFERED=1
# .pyc を事前生成してコールドスタートを短縮する
ENV UV_COMPILE_BYTECODE=1

# 依存の解決はソースより前に置く。app/ を変更しても uv sync のレイヤーは再利用される。
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

# 非rootで実行する。/app は読み取りのみで足りるので chown は不要。
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Cloud Run は待ち受けポートを環境変数 PORT で指定してくるので、8000 決め打ちにしない。
# ${PORT:-8080} の展開にシェルが必要なため sh -c 形式にしている。
# uv run ではなく venv の uvicorn を直叩きする（uv run は毎回ロック検証が走り起動が遅い）。
CMD ["sh", "-c", ".venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
