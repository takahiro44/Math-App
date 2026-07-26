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
- 文部科学省の学習指導要領解説を参照して単元に沿った問題を生成
- 習っていない範囲の問題が出題されにくくなる
- 埋め込みは事前計算してリポジトリに同梱。実行時はベクトルDBも永続ディスクも不要

## 対象単元

| 学年 | 単元 |
|------|------|
| 中学1年生 | 正負の数、文字と式、方程式 |
| 中学2年生 | 式の計算、連立方程式 |
| 中学3年生 | 式の展開、因数分解、平方根、二次方程式 |

> 図形の描写やグラフの読み取りを必要とする問題は対象外。計算問題に特化しています。

単元マスタは `frontend/src/mathUnits.ts` が正。この表はその写しなので、追加・改名したら両方直してください。

## 技術スタック

### バックエンド
- **FastAPI** - APIサーバー
- **LangChain** - LLMオーケストレーション（PromptTemplate / LCEL / OutputParser）
- **Gemini 2.5 Flash** - 問題生成・採点
- **NumPy** - 事前計算した埋め込みに対するコサイン類似度検索（RAG用）
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

**3. Dockerビルド・起動**
```bash
docker compose up --build -d
```

検索インデックス（`backend/app/rag/data/`）はリポジトリに同梱されているので、
セットアップ時のベクトル化は不要です。指導要領PDFの差し替え時のみ
[検索インデックスの再構築](#検索インデックスの再構築) を実行してください。

**4. アクセス確認**

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

# パッケージ追加後の再ビルド
docker compose up --build -d
```

## 検索インデックスの再構築

指導要領PDFを差し替えたときだけ実行します。通常の開発・デプロイでは不要です。

**1. PDFを配置**

以下のURLからダウンロードして `rag/documents/math_guidelines.pdf` に配置します。

```
https://www.mext.go.jp/component/a_menu/education/micro_detail/__icsFiles/afieldfile/2019/03/18/1387018_004.pdf
```

文部科学省「中学校学習指導要領（平成29年告示）解説 数学編」（全229ページ）です。

**2. インデックスを構築**

```bash
cd backend
uv run --group build python scripts/build_index.py
```

`backend/app/rag/data/` に以下の2ファイルが出力されます。どちらもリポジトリにコミットします。

| ファイル | 内容 |
|---------|------|
| `guidelines_vectors.npz` | 埋め込み行列（float32・L2正規化済み） |
| `guidelines_chunks.json` | チャンク本文・ページ番号・出典情報 |

埋め込みAPIのレート制限で中断しても、チェックポイントから再開されるので再実行すれば続きから進みます。

## 出典

出典：「【数学編】中学校学習指導要領（平成29年告示）解説」（文部科学省）
https://www.mext.go.jp/component/a_menu/education/micro_detail/__icsFiles/afieldfile/2019/03/18/1387018_004.pdf
（2026年7月25日に利用）

本コンテンツは文部科学省ウェブサイト利用規約（政府標準利用規約第2.0版準拠、CC BY 4.0互換）に基づき利用しています。

## ライセンス

適用範囲がファイルによって異なります。

| 対象 | ライセンス |
|------|-----------|
| ソースコード（上記データを除くリポジトリ全体） | **MIT** — [LICENSE](LICENSE) |
| `backend/app/rag/data/guidelines_chunks.json`<br>`backend/app/rag/data/guidelines_vectors.npz` | **文部科学省ウェブサイト利用規約**（政府標準利用規約第2.0版準拠、CC BY 4.0互換）に基づき利用。**出典表示が必要** |

`backend/app/rag/data/` のデータは学習指導要領解説から機械的に抽出したもので、このリポジトリの著作物ではありません。出典は上記「[出典](#出典)」のとおりです。詳細は [`backend/app/rag/data/README.md`](backend/app/rag/data/README.md) に記載しています。
