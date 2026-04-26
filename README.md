# 数学問題生成アプリ

中学生向けの数学問題を自動生成するWebアプリケーションです。  
生成AIを活用して問題の作成・採点・解説を行い、演習と問題プリント作成の2つのモードを提供します。

## 機能

### 演習モード
- 学年・単元・難易度・問題数を選択して演習を開始
- AIが問題を一括生成し、1問ずつ順番に出題
- 回答を入力すると即座に採点（ハイブリッド採点方式）
- ヒントをトグルで表示・非表示
- 進捗バーで何問目かを確認
- 全問終了後に正答率と結果を表示

### プリント作成モード
- 学年・単元・難易度・問題数を選択してプリントを生成
- 問題用紙・解答解説用紙をそれぞれ印刷・PDF保存
- 数式はKaTeXで正しくレンダリング

### RAG（学習指導要領連携）
- 文部科学省の学習指導要領PDFを参照して単元に沿った問題を生成
- 習っていない範囲の問題が出題されにくくなる

## 対象単元

| 学年 | 単元 |
|------|------|
| 中学1年生 | 正の数・負の数、文字と式、方程式 |
| 中学2年生 | 式の計算、連立方程式 |
| 中学3年生 | 多項式の計算、平方根、二次方程式 |

> 図形の描写やグラフの読み取りを必要とする問題は対象外。計算問題に特化しています。

## 技術スタック

### バックエンド
- **FastAPI** - APIサーバー
- **LangChain** - LLMオーケストレーション（PromptTemplate / LCEL / OutputParser）
- **Gemini 2.5 Flash** - 問題生成・採点
- **ChromaDB** - ベクトルデータベース（RAG用）
- **uv** - パッケージ管理

### フロントエンド
- **React + TypeScript** - UIフレームワーク
- **Vite** - ビルドツール
- **Tailwind CSS** - スタイリング
- **KaTeX** - 数式レンダリング
- **React Router** - ページ遷移

### インフラ
- **Docker / Docker Compose** - コンテナ化

## セットアップ

### 前提条件
- Docker Desktop がインストールされていること
- Google Gemini API キーを取得していること

### 手順

**1. リポジトリをクローン**
```bash
git clone https://github.com/takahiro44/Math-App.git
cd Math-App
```

**2. 環境変数を設定**
```bash
cp .env.example .env
# .env を編集して GOOGLE_API_KEY を設定
```

**3. 学習指導要領PDFを配置**

以下のURLからPDFをダウンロードして `rag/documents/math_guidelines.pdf` に配置してください。

```
https://www.mext.go.jp/content/1413522_007.pdf
```

**4. Dockerビルド・起動**
```bash
docker compose up --build -d
```

**5. RAGのベクトル化（初回のみ）**
```bash
docker compose exec backend uv run python -m app.rag.ingest
```

**6. アクセス確認**

| サービス | URL |
|---------|-----|
| フロントエンド | http://localhost:5173 |
| バックエンド | http://localhost:8000 |
| API ドキュメント | http://localhost:8000/docs |

## 環境変数

`.env.example` をコピーして `.env` を作成してください。

```
GOOGLE_API_KEY=your_api_key_here
```

## APIエンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /health | ヘルスチェック |
| POST | /question/generate | 問題を1問生成 |
| POST | /grading/grade | 回答を採点 |
| POST | /print/generate | 複数問をまとめて生成 |

## 採点方式

ハイブリッド採点を採用しています。

1. **文字列一致**：正規化した文字列が一致する場合は即座に正解判定（LLM不使用）
2. **LLM採点**：一致しない場合のみGeminiが採点（表記ゆれ・記述式に対応）

正規化では以下を処理します。
- `$` 記号の除去（LaTeX記法対応）
- `\frac{a}{b}` → `a/b` への変換
- 全角文字の半角変換
- スペースの除去

## 開発コマンド

```bash
# 起動
docker compose up -d

# 停止
docker compose down

# バックエンドのログ確認
docker compose logs backend

# RAGの再ベクトル化
docker compose exec backend uv run python -m app.rag.ingest

# パッケージ追加後の再ビルド
docker compose up --build -d
```

## ライセンス

MIT
