# デプロイ手順

バックエンドを Google Cloud Run、フロントエンドを Vercel にデプロイする。
すべて手動実行の手順。GitHub Actions からの自動デプロイは未対応（Workload Identity の
設定が必要なので、まず手動で通す方針）。

前提として、バックエンドはステートレスで永続ディスクを必要としない。検索インデックスは
イメージに同梱されているので、デプロイ時にベクトル化は走らない。

## 全体像

| | 配置先 | 何を渡すか |
|---|--------|-----------|
| バックエンド | Cloud Run | `GOOGLE_API_KEY`、CORS 設定、パスコード |
| フロントエンド | Vercel | `VITE_API_BASE_URL`（Cloud Run の URL） |

**順序に注意**: フロントの `VITE_API_BASE_URL` には Cloud Run の URL が必要で、
バックエンドの `ALLOWED_ORIGINS` には Vercel の URL が必要。相互に依存するので
「バックエンドを先にデプロイ → URL を得る → Vercel をデプロイ → その URL で
バックエンドの環境変数を更新」の順で進める。

## 現在の構成（2026-07-26 時点）

| 項目 | 値 |
|------|-----|
| GCP プロジェクト | `math-app-backend` |
| リージョン | `asia-northeast1` |
| Cloud Run サービス | `math-app-backend` |
| **バックエンド URL** | https://math-app-backend-1061641828981.asia-northeast1.run.app |
| Artifact Registry | `cloud-run-source-deploy`（最新3世代保持ポリシー適用済み） |
| シークレット | `GOOGLE_API_KEY` / `APP_PASSCODE` |
| 予算アラート | 月1,000円・50%/90%/100% で通知 |
| Vercel チーム | `takahiro44s-projects` |
| **フロントエンド URL** | https://math-app-chi-eight.vercel.app |
| `ALLOWED_ORIGINS` | `https://math-app-chi-eight.vercel.app` |
| `ALLOWED_ORIGIN_REGEX` | `https://math-[a-z0-9-]+-takahiro44s-projects\.vercel\.app` |

Vercel のデプロイURLは `https://math-<hash>-takahiro44s-projects.vercel.app` の形式で、
プロジェクト名が `math-app` でも `math-` に切り詰められる。正規表現はこれに合わせてある。

**残作業**: GitHub のリポジトリ変数 `BACKEND_URL` の設定（keep-alive 用）。

---

## 1. バックエンド（Cloud Run）

### 1-1. 事前準備

```bash
# 使うプロジェクトとリージョンを決める
export PROJECT_ID=math-app-backend
export REGION=asia-northeast1
export SERVICE=math-app-backend

gcloud config set project "$PROJECT_ID"
gcloud config set run/region "$REGION"

# 必要なAPIを有効化（--source デプロイは Cloud Build も使う）
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudbuild.googleapis.com
```

**課金アカウントの紐付けを先に確認すること。** プロジェクトを作っただけでは
紐付いていない。未リンクだとデプロイが権限エラーで落ちる。

```bash
gcloud billing projects describe "$PROJECT_ID"   # billingEnabled: true であること
```

> 課金アカウント1つに紐付けられるプロジェクト数には上限がある（セルフサービスの
> 既定で5件）。超えていると `Cloud billing quota exceeded` で
> `gcloud billing projects link` が失敗する。その場合は不要なプロジェクトの
> 課金を解除するか、コンソールから操作する。

### 1-2. Artifact Registry のリポジトリについて

**リポジトリは自分で作らなくてよい。** `gcloud run deploy --source` は
`cloud-run-source-deploy` という名前のリポジトリを**自動で作る**（初回デプロイ時に
確認プロンプトが出る）。自分で別名のリポジトリを作っても `--source` デプロイは
そちらを使わないので、空のまま残るだけになる。

したがって順序は「先にデプロイ（1-5）→ 自動作成されたリポジトリにポリシーを適用」
になる。**初回デプロイの直後、2回目のデプロイをする前に必ず設定すること。**

### 1-3. クリーンアップポリシー（初回デプロイ直後に必ず入れる）

イメージはレジストリ上で約 158MiB（ローカルの 644MB は非圧縮サイズ）。
Artifact Registry の無料枠は 0.5GB なので、**4世代目で超過して課金が始まる。**

`cleanup-policy.json` を作る。

```json
[
  {
    "name": "keep-recent-versions",
    "action": { "type": "Keep" },
    "mostRecentVersions": {
      "keepCount": 3
    }
  },
  {
    "name": "delete-all-others",
    "action": { "type": "Delete" },
    "condition": {
      "tagState": "ANY"
    }
  }
]
```

> `condition` に `"olderThan": "0s"` を書くと `INVALID_ARGUMENT: empty condition` で
> 弾かれる。0 は「条件なし」と解釈されるため。`tagState: "ANY"` を使うこと。

適用する。リポジトリ名は `--source` デプロイが作った `cloud-run-source-deploy`。

```bash
export REPO=cloud-run-source-deploy

# まず dry-run で「何が削除されるか」を確認する
gcloud artifacts repositories set-cleanup-policies "$REPO" \
  --location="$REGION" \
  --policy=cleanup-policy.json \
  --dry-run

# 問題なければ本適用。--no-dry-run を明示すること
gcloud artifacts repositories set-cleanup-policies "$REPO" \
  --location="$REGION" \
  --policy=cleanup-policy.json \
  --no-dry-run

# 確認: cleanupPolicyDryRun が出力に現れなければ本番適用されている
gcloud artifacts repositories describe "$REPO" --location="$REGION"
```

> **`--dry-run` はリポジトリの設定として保存される。** 一度 dry-run で流すと
> `cleanupPolicyDryRun: true` が残り、次に `--dry-run` なしで適用しても
> **その状態のまま**になる。`--no-dry-run` を明示的に渡して解除すること。
> `describe` の出力に `cleanupPolicyDryRun` が出ていたら、まだ実際には削除されない。

`Keep` ポリシーが `Delete` より優先されるので、この2つの組み合わせで
「最新3世代だけ残して他は削除」になる。ポリシーの実行は即時ではなく、
Artifact Registry 側で非同期に走る。

> 手動で今すぐ消したい場合:
> ```bash
> gcloud artifacts docker images list "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE" \
>   --include-tags --sort-by=~UPDATE_TIME
> gcloud artifacts docker images delete \
>   "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE@sha256:..." --delete-tags
> ```

### 1-4. シークレットの登録

`GOOGLE_API_KEY` は Secret Manager に置く。`--set-env-vars` で直接渡すと
`gcloud run services describe` やコンソールで平文が見えてしまう。

```bash
# API キーを登録（ローカルの .env から読むならこの形）
set -a; . ../.env; set +a
printf '%s' "$GOOGLE_API_KEY" | \
  gcloud secrets create GOOGLE_API_KEY --data-file=-

# 公開デモ用の共有パスコードを使う場合のみ（任意）
printf '%s' 'YOUR_SHARED_PASSCODE' | \
  gcloud secrets create APP_PASSCODE --data-file=-

# Cloud Run のサービスアカウントに読み取り権限を与える
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
for s in GOOGLE_API_KEY; do   # APP_PASSCODE を作ったならここに足す
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
done
```

`APP_PASSCODE` は任意。設定しなければ認証なしで動き、保護はレートリミットのみに
なる。URL を知られた時点で誰でも API を叩けるので、**広く共有する前には設定する。**

値を更新するときは新しいバージョンを追加する。

```bash
printf '%s' 'NEW_VALUE' | gcloud secrets versions add GOOGLE_API_KEY --data-file=-
# 反映するには再デプロイ（または --update-secrets で latest を指し直す）
```

### 1-5. デプロイ

`backend/` をソースにしてデプロイする。`gcloud run deploy --source` は
Cloud Build でイメージをビルドして Artifact Registry に push する。

初回は Vercel の URL がまだ無いので、CORS 設定は後回しでよい（curl での確認には
CORS は関係ない）。まずデプロイして URL を得る。

```bash
cd backend

gcloud run deploy "$SERVICE" \
  --source . \
  --region="$REGION" \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 3 \
  --timeout 300 \
  --set-secrets "GOOGLE_API_KEY=GOOGLE_API_KEY:latest" \
  --set-env-vars "RATE_LIMIT_PER_MINUTE=20"
```

Vercel の URL が確定したあと、CORS とパスコードを足す（`APP_PASSCODE` を
使う場合）。

```bash
gcloud run services update "$SERVICE" --region="$REGION" \
  --update-secrets "APP_PASSCODE=APP_PASSCODE:latest" \
  --update-env-vars "^@^ALLOWED_ORIGINS=https://your-app.vercel.app@ALLOWED_ORIGIN_REGEX=https://your-app-[a-z0-9-]+\.vercel\.app"
```

パラメータの意図:

| パラメータ | 理由 |
|-----------|------|
| `--memory 512Mi` | 実測 idle 183MB / リクエスト後 190MB。512Mi で十分な余裕がある |
| `--cpu 1` | LLM 待ちが支配的で CPU は使わない |
| `--min-instances 0` | ゼロスケールで課金を抑える。コールドスタートは keep-alive で緩和 |
| `--max-instances 3` | **API キー乱用時のコスト上限として機能する。** 低く抑えることが目的 |
| `--timeout 300` | 問題生成に 10〜20 秒かかる。デフォルト 300s のままで足りる |
| `--allow-unauthenticated` | 公開デモなので IAM 認証は使わず、アプリ側のパスコードで仕切る |

> `--set-env-vars` はカンマ区切りで解釈されるため、値にカンマを含めるときは
> 区切り文字を変える必要がある。`ALLOWED_ORIGINS` に複数ドメインを入れる場合は
> `--set-env-vars "^@^ALLOWED_ORIGINS=https://a.example,https://b.example@..."` の
> ように先頭で区切り文字を指定する。

デプロイ後に URL を取得する。

```bash
gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)'
```

### 1-6. 環境変数だけ更新したいとき

```bash
gcloud run services update "$SERVICE" --region="$REGION" \
  --update-env-vars "ALLOWED_ORIGINS=https://your-app.vercel.app"
```

---

## 2. フロントエンド（Vercel）

リポジトリのルートに `frontend/` があるモノレポ構成なので、Root Directory の
設定が必要。

### 2-1. プロジェクト設定

| 項目 | 値 |
|------|-----|
| Framework Preset | Vite |
| **Root Directory** | `frontend` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Install Command | `npm ci`（デフォルトのままでよい） |

### 2-2. 環境変数

Project Settings > Environment Variables に設定する。

| 変数 | 値 | 対象環境 |
|------|-----|---------|
| `VITE_API_BASE_URL` | Cloud Run の URL（末尾スラッシュなし） | Production / Preview / Development |
| `VITE_APP_PASSCODE` | バックエンドの `APP_PASSCODE` と同じ値 | Production / Preview |

**`VITE_API_BASE_URL` が未設定だとビルドが失敗する**（`vite.config.ts` で
明示的に落としている）。デプロイ後に初めて壊れるより、ビルド時に気づくほうがよい。

> `VITE_APP_PASSCODE` はビルド成果物に埋め込まれ、DevTools から見える。
> bot による直叩きを防ぐ仕切りであって、秘密の保護ではない。

### 2-3. デプロイ後にバックエンドの CORS を更新する

Vercel の URL が確定したら、バックエンド側に反映する。

```bash
gcloud run services update "$SERVICE" --region="$REGION" \
  --update-env-vars "ALLOWED_ORIGINS=https://your-app.vercel.app"
```

プレビューデプロイは `https://your-app-<hash>-<org>.vercel.app` のような動的ドメインに
なるため、完全一致では受けられない。`ALLOWED_ORIGIN_REGEX` で受ける。

```bash
# 実際のプレビューURLの形を確認してから正規表現を決めること
gcloud run services update "$SERVICE" --region="$REGION" \
  --update-env-vars 'ALLOWED_ORIGIN_REGEX=https://your-app-[a-z0-9-]+\.vercel\.app'
```

正規表現は Starlette の `allow_origin_regex` にそのまま渡され、**完全一致**で
評価される（内部で `re.fullmatch` 相当）。`.*` を安易に使うと任意のドメインから
呼べてしまうので、プロジェクト名の接頭辞を必ず含める。

---

## 3. keep-alive の設定

`.github/workflows/keep-alive.yml` が 10 分ごとに `/health` を叩く。

GitHub のリポジトリ設定で **Settings > Secrets and variables > Actions > Variables** に
以下を追加する。

| 変数名 | 値 |
|--------|-----|
| `BACKEND_URL` | Cloud Run の URL |

注意点:

- scheduled workflow は**リポジトリが60日間非アクティブだと自動停止する**。停止したら
  Actions 画面から手動で再有効化する。
- cron の実行時刻は混雑状況により数分〜十数分遅延する。厳密な間隔は保証されない。
- `lru_cache` はプロセス単位なので、インスタンスが入れ替わると埋め込みクエリの
  キャッシュは空になり cold のレイテンシ（約 0.5 秒）を再度払う。これは許容している。

---

## 4. デプロイ後の疎通確認

```bash
export BACKEND_URL=$(gcloud run services describe "$SERVICE" --region="$REGION" --format='value(status.url)')
export PASSCODE=YOUR_SHARED_PASSCODE
```

### 4-1. ヘルスチェック（認証なしで通るはず）

```bash
curl -i "$BACKEND_URL/health"
# → 200 {"status":"ok"}
```

### 4-2. パスコードなしで API を叩く（弾かれるはず）

```bash
curl -i -X POST "$BACKEND_URL/print/generate" \
  -H 'Content-Type: application/json' \
  -d '{"grade":1,"unit":"正負の数","difficulty":"normal","num_questions":3}'
# → 401 {"detail":"X-App-Passcode ヘッダが不正です"}
```

### 4-3. パスコードありで API を叩く（通るはず）

```bash
curl -X POST "$BACKEND_URL/print/generate" \
  -H 'Content-Type: application/json' \
  -H "X-App-Passcode: $PASSCODE" \
  -d '{"grade":3,"unit":"平方根","difficulty":"normal","num_questions":3}'
# → 200 {"questions":[...]}
```

### 4-4. CORS プリフライトの確認

```bash
# 本番ドメイン（完全一致）
curl -i -X OPTIONS "$BACKEND_URL/print/generate" \
  -H 'Origin: https://your-app.vercel.app' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type,x-app-passcode'
# → 200 で access-control-allow-origin ヘッダが返る

# プレビュードメイン（正規表現）
curl -i -X OPTIONS "$BACKEND_URL/print/generate" \
  -H 'Origin: https://your-app-abc123-yourorg.vercel.app' \
  -H 'Access-Control-Request-Method: POST'
# → access-control-allow-origin が返る

# 許可していないドメイン
curl -i -X OPTIONS "$BACKEND_URL/print/generate" \
  -H 'Origin: https://evil.example' \
  -H 'Access-Control-Request-Method: POST'
# → access-control-allow-origin が返らない
```

### 4-5. レートリミットの確認

```bash
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "$i: %{http_code}\n" "$BACKEND_URL/question/generate" \
    -X POST -H 'Content-Type: application/json' -H "X-App-Passcode: $PASSCODE" \
    -d '{"grade":1,"unit":"正負の数","difficulty":"easy"}'
done
# → 21回目以降が 429 になる（RATE_LIMIT_PER_MINUTE=20 の場合）
```

**レートリミットはインスタンス単位**なので、`--max-instances 3` なら実効上限は
最大で 3 倍になる。事故防止が目的であり厳密な制限ではない。

### 4-6. ログの確認

```bash
gcloud run services logs read "$SERVICE" --region="$REGION" --limit=50

# 起動時にインデックスが読めているか
gcloud run services logs read "$SERVICE" --region="$REGION" --limit=200 \
  | grep 'RAGインデックス'
# → "RAGインデックスを読み込みました: 659 チャンク, 3072 次元"

# 検索結果が単元と対応しているか
gcloud run services logs read "$SERVICE" --region="$REGION" --limit=200 | grep '\[RAG\]'

# レイテンシの内訳
gcloud run services logs read "$SERVICE" --region="$REGION" --limit=200 | grep '\[PERF\]'
```

---

## 5. ロールバック

```bash
# リビジョン一覧
gcloud run revisions list --service="$SERVICE" --region="$REGION"

# 特定リビジョンに全トラフィックを戻す
gcloud run services update-traffic "$SERVICE" --region="$REGION" \
  --to-revisions=math-app-backend-00003-abc=100
```

---

## 6. 費用に効くポイント

| 項目 | 対処 |
|------|------|
| Artifact Registry のストレージ | クリーンアップポリシーで最新3世代のみ保持（1-3） |
| Cloud Run のインスタンス数 | `--max-instances 3` でコスト上限を作る |
| Gemini API の乱用 | パスコード + レートリミット。max-instances も間接的な上限になる |
| アイドル時の課金 | `--min-instances 0`。keep-alive の 10 分間隔リクエストぶんだけ課金される |
