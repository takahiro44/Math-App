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
- ルーティングは `App.tsx`: `/`(Home) `/practice` `/print` の3ページ。
- 単元マスタは `frontend/src/mathUnits.ts`（学年→単元名の配列）。バックエンドにはこの一覧はなく、フロントから `unit` 文字列として渡される。
- 難易度は `easy`/`normal`/`hard` の文字列で送られ、バックエンドの `get_difficulty_guideline()`（`prompts/question.py`）が詳細ガイドライン文字列に展開してプロンプトに埋め込む。
- 演習の状態遷移は `Practice.tsx` の `PracticeState`（`setup`→`loading`→`practicing`→`result`）で管理し、正誤はクライアント側で集計する。
