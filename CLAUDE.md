# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

中学生（1〜3年）向けの数学**計算問題**を生成AI（Gemini 2.5 Flash）で自動生成・採点・解説するWebアプリ。「演習モード」と「プリント作成モード」の2機能を持つ。図形・グラフ・文章題は対象外で、計算問題に特化している。

### 解決している課題

個別指導塾の講師が、生徒の苦手に合わせた演習プリントを宿題として渡したいが、問題集の選定・該当問題の選定・印刷という3工程を授業間の10分の休み時間でこなす必要があり、生徒を待たせてしまうことがある。この準備時間を削るためのアプリ。

## Repository layout

3つの独立したパートで構成される。
- `backend/` — FastAPI + LangChain。問題生成・採点・PDF出力のAPI。`uv` で依存管理。
- `frontend/` — React 19 + TypeScript + Vite + Tailwind CSS v4。
- `rag/` — 学習指導要領PDF (`documents/math_guidelines.pdf`) の置き場。**インデックス構築時にしか使わない**ので、実行時には参照されない（compose では構築用にマウントしているだけ）。検索インデックス本体は `backend/app/rag/data/` にコミット済み。

## Commands

開発は基本的に Docker Compose 経由で行う。

```bash
docker compose up --build -d          # 初回・依存追加後（ビルド込み）起動
docker compose up -d                  # 通常起動
docker compose down                   # 停止
docker compose logs backend           # バックエンドのログ
```

検索インデックスはリポジトリに同梱されているので、**起動前のベクトル化は不要**。指導要領PDFを差し替えたときだけ再構築する。

```bash
cd backend && uv run --group build python scripts/build_index.py   # インデックス再構築
```

- フロント: http://localhost:5173 / バックエンド: http://localhost:8000 / API docs: http://localhost:8000/docs
- バックエンドは compose の `command` で `--reload` を付けて起動し、`backend/app` がマウントされているのでコード変更は即反映される。
- **compose の command で `uv run` は使えない。** コンテナは非rootで動くため `/app/.venv` に書き込めず、`uv run` が起動時に環境を同期しようとして失敗する。`.venv/bin/uvicorn` を直叩きしている。
- フロントエンドの lint: `docker compose exec frontend npm run lint`。**現状 `no-irregular-whitespace` で6件失敗する**（全角スペース。今回のリファクタ以前から存在）。テストフレームワークは未導入。
- compose のフロントは `frontend/` をマウントしていないので、フロントのコード変更は `docker compose up --build -d` が必要。

## デプロイ

フロントエンドは **Vercel**、バックエンドは **Google Cloud Run**。手順は `docs/deploy.md`。compose は開発専用。

- `backend/Dockerfile` の `CMD` は `--reload` なしで、**Cloud Run が渡す環境変数 `PORT`**（デフォルト8080）を `sh -c` 経由で受ける。非rootユーザー `appuser` で動く。
- `frontend/Dockerfile` は compose 専用。本番では Vercel が直接ビルドするので使わない。
- `--max-instances` は API キー乱用時のコスト上限として機能させるため低く抑える（3）。

## 環境変数

`.env.example` / `frontend/.env.example` に全項目とデフォルト値を記載してある。

バックエンド（ルート `.env` / Cloud Run）:

| 変数 | 必須 | 備考 |
|---|---|---|
| `GOOGLE_API_KEY` | ✅ | Gemini + Embedding |
| `ALLOWED_ORIGINS` | | CORS 完全一致（カンマ区切り）。デフォルト `http://localhost:5173,http://localhost:4173` |
| `ALLOWED_ORIGIN_REGEX` | | Vercel プレビューの動的ドメイン用。デフォルトなし |
| `APP_PASSCODE` | | 公開デモ用の共有パスコード。**未設定なら認証なし**（開発時はこれ） |
| `RATE_LIMIT_PER_MINUTE` | | デフォルト20、`0` で無効 |
| `LOG_LEVEL` | | デフォルト INFO |

フロント（`frontend/.env` / Vercel）:

| 変数 | 備考 |
|---|---|
| `VITE_API_BASE_URL` | 開発時は未設定なら `http://localhost:8000` にフォールバック。**本番ビルドでは未設定だと `vite.config.ts` がビルドを失敗させる** |
| `VITE_APP_PASSCODE` | バックエンドの `APP_PASSCODE` と同じ値。**ビルド成果物に埋め込まれ DevTools から見える**（bot 対策であって秘密の保護ではない） |

## Architecture

### バックエンドのAPI構成
`app/main.py` が3つのルーターを prefix 付きで束ねる。各ルーターは「LangChain の LCEL チェーン（`prompt | llm | parser`）を組んで `invoke` する」という同じ形。
- `POST /question/generate` — 1問生成（`single_question_prompt`）。
- `POST /print/generate` — 複数問を一括生成（`question_prompt`）。**演習モードもこの一括生成エンドポイントを使う**（フロントの `Practice.tsx` が `/print/generate` を叩き、取得した全問をクライアント側で1問ずつ出題する）。`/question/generate` は現状フロントから未使用。
- `POST /grading/grade` — 採点。
- 各層は `routers/` `prompts/` `schemas/` に分かれ、単元ごとではなく機能ごとに分割されている。

### ミドルウェア（`app/middleware.py`）— 公開デモの事故防止
`PasscodeAuthMiddleware`（共有パスコード）と `RateLimitMiddleware`（IPごと・インメモリ）。**どちらも環境変数が未設定なら無効**になり、開発を妨げない。セキュリティ機構ではなく Gemini API キー乱用の事故防止が目的。

壊れやすい点が3つある。

- **`add_middleware` の順序**: Starlette は**最後に追加したものが最も外側**になる。CORS を最後に追加していないと 401/429 のレスポンスに CORS ヘッダが付かず、ブラウザ側では原因不明の「CORS エラー」になる。`main.py` は認証 → レートリミット → CORS の順で追加している。
- **`OPTIONS` の免除**: CORS プリフライトはカスタムヘッダを載せてこない。認証で弾くとブラウザからのリクエストが全滅する。
- **クライアントIPは `X-Forwarded-For` の左端**から取る。Cloud Run はプロキシ経由なので `request.client.host` はプロキシのIPになり、全リクエストが同一IPに見えてレートリミットが機能しない。

`/health` は認証・レートリミットの両方を免除している（keep-alive の cron が叩くため）。レートリミットはプロセス単位なので、インスタンスが増えると実効上限も増える（許容済み）。

### コールドスタート対策
Cloud Run を `min-instances 0` で運用するため、`.github/workflows/keep-alive.yml` が10分ごとに `/health` を叩く。リポジトリ変数 `BACKEND_URL` が必要。`lru_cache` はプロセス単位なので、インスタンスが入れ替わると埋め込みクエリのキャッシュは失われ cold のレイテンシ（約0.5秒）を再度払う（許容済み）。

### RAG フロー（事前計算 + numpy。ベクトルDBは使わない）
**バックエンドはステートレス**で、永続ディスクを必要としない。埋め込みをビルド時に固めてリポジトリに同梱し、実行時は numpy の行列積で検索する。

構築（開発時のみ・`backend/scripts/build_index.py`）:
- pypdf で指導要領PDFのテキストを抽出 → 500字/オーバーラップ50 でチャンク化（ページ番号は1始まりで保持）→ Gemini `models/gemini-embedding-001` で埋め込み → **L2正規化して** `backend/app/rag/data/` に2ファイル出力。
  - `guidelines_vectors.npz` — float32 の埋め込み行列（現状 659チャンク × 3072次元・約7.5MB）
  - `guidelines_chunks.json` — チャンク本文・ページ番号・出典情報（人間がレビューできる形）
- レート制限で落ちてもバッチ単位でチェックポイントを書くので、再実行すれば続きから再開する。
- pypdf と langchain-text-splitters は `build` 依存グループにあり、**実行時イメージには入らない**（`uv sync --no-dev` の対象外）。

検索（実行時・`app/rag/retriever.py`）:
- 公開インターフェースは `retrieve(query: str, k: int = 3) -> list[str]` のみ。任意のクエリ文字列で引けるので、将来「講師の自由記述が指定学年の範囲を超えていないか検証する」用途にも使える。
- ベクトル・チャンク・embeddings クライアントは**モジュールロード時に一度だけ**初期化する。リクエストごとに作らないこと。
- 構築時に正規化済みなので、検索はクエリベクトルを正規化して `vectors @ q` の**行列積1回**でコサイン類似度になる。
- クエリ埋め込みは `functools.lru_cache` 済み。現状のクエリは「中学{grade}年生 {unit}」で組み合わせが9通りしかないため、2回目以降はAPI呼び出しゼロ（実測 1.06s → 0.004s）。**失敗をキャッシュしないため `_embed_query` は例外を投げる設計**にしてある（lru_cache は例外をキャッシュしない）。
- インデックス欠損・埋め込みAPI失敗のどちらでも**例外を投げず空リストを返す**。呼び出し側は context なしで生成を続行する。理由は必ずログに残す。
- パスは `Path(__file__).parent / "data"` 基準。`/app/rag/...` のハードコードは廃止済み。
- 検索されたチャンクは `[RAG] query=... rank=... score=... page=...` の形で INFO ログに出るので、単元との対応を目視確認できる。

`backend/tests/fixtures/retrieval_baseline.json` は ChromaDB 版の検索結果のスナップショット（`scripts/capture_baseline.py` が生成）。numpy 実装への移行時に全9クエリ×上位3件が**順位まで100%一致**することを確認済み。検索まわりを変更したらこれと比較すること。

### 採点ロジック（ハイブリッド）
`routers/grading.py` の `normalize()` で文字列一致を先に試し、一致すれば LLM を呼ばず即正解にする。不一致のときだけ Gemini で採点。正規化は `$` 除去・`\frac{a}{b}`→`a/b`・LaTeXコマンド除去・全角→半角・空白除去を行う。表記ゆれ対応の要なので、採点まわりを変更するときはこの正規化と LLM フォールバックの両方に注意。

### LaTeX / JSON エスケープの取り扱い（重要な壊れやすいポイント）
数式は `$...$`（インライン）/ `$$...$$`（ブロック）の LaTeX で全体をやり取りする。JSON 経由でバックスラッシュが壊れやすいため、両端で防御している。
- **プロンプト側** (`prompts/question.py`): LLM にバックスラッシュを2重で出力させるよう強く指示している。
- **バックエンド側**: `_preprocess` → `_restore_latex_escapes` を parser の前段に挟み、`\f`+`rac` のような制御文字化した壊れた出力を `\\frac` に戻す。パーサは `RunnableLambda(_preprocess) | JsonOutputParser` の形。
- **フロント側** (`components/MathText.tsx`): `$`/`$$` で分割し `react-katex` の `InlineMath`/`BlockMath` でレンダリング。通常テキスト中の `\n` や `\\` は改行に変換。
- 数式表示が崩れる不具合は、この3箇所のどこかのエスケープ処理が原因であることが多い。

### フロントエンド
- **API 呼び出しは `config.ts` の `apiFetch(path, init)` を使う。** `fetch` を直接呼ばないこと。ベースURLの結合・`Content-Type`・パスコードヘッダの付与をここに集約している。
- ルーティングは `App.tsx`: `/`(Home) `/practice` `/print` の3ページ。
- 単元マスタは `frontend/src/mathUnits.ts`（学年→単元名の配列）。バックエンドにはこの一覧はなく、フロントから `unit` 文字列として渡される。
- 難易度は `easy`/`normal`/`hard` の文字列で送られ、バックエンドの `get_difficulty_guideline()`（`prompts/question.py`）が詳細ガイドライン文字列に展開してプロンプトに埋め込む。
- 演習の状態遷移は `Practice.tsx` の `PracticeState`（`setup`→`loading`→`practicing`→`result`）で管理し、正誤はクライアント側で集計する。

## ライセンスの適用範囲

ソースコードは MIT（`LICENSE`）。ただし **`backend/app/rag/data/` のデータは MIT の対象外**で、文部科学省ウェブサイト利用規約（政府標準利用規約第2.0版準拠、CC BY 4.0互換）に基づき利用しており**出典表示が必要**。詳細は `backend/app/rag/data/README.md`。「指導要領準拠」が売りなので、出典表記を壊さないこと。
