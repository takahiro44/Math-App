# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

中学生（1〜3年）向けの数学**計算問題**を生成AI（Gemini 2.5 Flash）で自動生成・採点・解説するWebアプリ。「演習モード」と「プリント作成モード」の2機能を持つ。図形・グラフ・文章題は対象外で、計算問題に特化している。

## Repository layout

3つの独立したパートで構成される。
- `backend/` — FastAPI + LangChain。問題生成・採点・PDF出力のAPI。`uv` で依存管理。
- `frontend/` — React 19 + TypeScript + Vite + Tailwind CSS v4。
- `rag/` — 学習指導要領PDF (`documents/math_guidelines.pdf`) と ChromaDB のベクトルストア (`vectorstore/`)。どちらもボリュームとしてバックエンドコンテナにマウントされる。

## Commands

開発は基本的に Docker Compose 経由で行う。

```bash
docker compose up --build -d          # 初回・依存追加後（ビルド込み）起動
docker compose up -d                  # 通常起動
docker compose down                   # 停止
docker compose logs backend           # バックエンドのログ
docker compose exec backend uv run python -m app.rag.ingest   # RAGの（再）ベクトル化。初回必須
```

- フロント: http://localhost:5173 / バックエンド: http://localhost:8000 / API docs: http://localhost:8000/docs
- バックエンドは `--reload` で起動し、`backend/app` がマウントされているのでコード変更は即反映される。
- フロントエンドの lint: `docker compose exec frontend npm run lint`（または `frontend/` で `npm run lint`）。テストフレームワークは未導入。
- 本番ビルド: `frontend/` で `npm run build`（`tsc -b && vite build`）。フロントは vite preview で配信される。

## 環境変数（必須）

- ルート `.env`: `GOOGLE_API_KEY`（Gemini + Embedding 用）。任意で `ALLOWED_ORIGINS`（CORS、カンマ区切り、デフォルト `http://localhost:5173`）。
- フロント `frontend/.env` / `.env.production`: `VITE_API_BASE_URL`。**未設定だと API 呼び出しが壊れる**（`config.ts` がそのまま参照するだけでフォールバックなし）。

## Architecture

### バックエンドのAPI構成
`app/main.py` が3つのルーターを prefix 付きで束ねる。各ルーターは「LangChain の LCEL チェーン（`prompt | llm | parser`）を組んで `invoke` する」という同じ形。
- `POST /question/generate` — 1問生成（`single_question_prompt`）。
- `POST /print/generate` — 複数問を一括生成（`question_prompt`）。**演習モードもこの一括生成エンドポイントを使う**（フロントの `Practice.tsx` が `/print/generate` を叩き、取得した全問をクライアント側で1問ずつ出題する）。`/question/generate` は現状フロントから未使用。
- `POST /grading/grade` — 採点。
- 各層は `routers/` `prompts/` `schemas/` に分かれ、単元ごとではなく機能ごとに分割されている。

### RAG フロー
`rag/ingest.py` が指導要領PDFを 500字/オーバーラップ50 でチャンク化 → Gemini embedding でベクトル化 → `rag/vectorstore` に永続化。生成時は `rag/retriever.py` の retriever が「中学{grade}年生 {unit}」で上位3件を取得し、プロンプトの `{context}` に注入する。**パスは `/app/rag/...` とコンテナ絶対パスでハードコードされている**ため、ingest はコンテナ内で実行する必要がある。ベクトルストアが空だと問題生成の質が落ちる。

### 採点ロジック（ハイブリッド）
`routers/grading.py` の `normalize()` で文字列一致を先に試し、一致すれば LLM を呼ばず即正解にする。不一致のときだけ Gemini で採点。正規化は `$` 除去・`\frac{a}{b}`→`a/b`・LaTeXコマンド除去・全角→半角・空白除去を行う。表記ゆれ対応の要なので、採点まわりを変更するときはこの正規化と LLM フォールバックの両方に注意。

### LaTeX / JSON エスケープの取り扱い（重要な壊れやすいポイント）
数式は `$...$`（インライン）/ `$$...$$`（ブロック）の LaTeX で全体をやり取りする。JSON 経由でバックスラッシュが壊れやすいため、両端で防御している。
- **プロンプト側** (`prompts/question.py`): LLM にバックスラッシュを2重で出力させるよう強く指示している。
- **バックエンド側**: `_preprocess` → `_restore_latex_escapes` を parser の前段に挟み、`\f`+`rac` のような制御文字化した壊れた出力を `\\frac` に戻す。パーサは `RunnableLambda(_preprocess) | JsonOutputParser` の形。
- **フロント側** (`components/MathText.tsx`): `$`/`$$` で分割し `react-katex` の `InlineMath`/`BlockMath` でレンダリング。通常テキスト中の `\n` や `\\` は改行に変換。
- 数式表示が崩れる不具合は、この3箇所のどこかのエスケープ処理が原因であることが多い。

### フロントエンド
- ルーティングは `App.tsx`: `/`(Home) `/practice` `/print` の3ページ。
- 単元マスタは `frontend/src/mathUnits.ts`（学年→単元名の配列）。バックエンドにはこの一覧はなく、フロントから `unit` 文字列として渡される。
- 難易度は `easy`/`normal`/`hard` の文字列で送られ、バックエンドの `get_difficulty_guideline()`（`prompts/question.py`）が詳細ガイドライン文字列に展開してプロンプトに埋め込む。
- 演習の状態遷移は `Practice.tsx` の `PracticeState`（`setup`→`loading`→`practicing`→`result`）で管理し、正誤はクライアント側で集計する。
