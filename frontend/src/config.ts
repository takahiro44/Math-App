// API のベース URL とリクエストの共通処理。
//
// 開発時：frontend/.env の VITE_API_BASE_URL が読まれる。未設定なら localhost:8000 に
//         フォールバックするので、.env なしでも動く。
// 本番時：ビルド時に VITE_API_BASE_URL が必須。未設定なら vite.config.ts が
//         ビルドを失敗させる（デプロイ後に初めて壊れるのを防ぐため）。

const DEV_FALLBACK = 'http://localhost:8000'

function resolveBaseUrl(): string {
  const configured = import.meta.env.VITE_API_BASE_URL
  if (configured) return configured.replace(/\/$/, '')

  if (import.meta.env.DEV) {
    console.warn(`VITE_API_BASE_URL が未設定です。${DEV_FALLBACK} を使います。`)
    return DEV_FALLBACK
  }

  // vite.config.ts で弾いているのでここには来ない想定だが、
  // undefined が URL に混ざって原因不明の失敗になるのは避ける。
  throw new Error('VITE_API_BASE_URL が未設定のままビルドされています。')
}

export const API_BASE_URL = resolveBaseUrl()

// 公開デモではバックエンドが共有パスコードを要求する。未設定なら送らない（開発時）。
const APP_PASSCODE = import.meta.env.VITE_APP_PASSCODE ?? ''

/**
 * API 呼び出しの共通ラッパ。ベースURLの結合とパスコードヘッダの付与をここに集約する。
 *
 * @param path 先頭が / のAPIパス（例: '/print/generate'）
 */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers)
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (APP_PASSCODE) {
    headers.set('X-App-Passcode', APP_PASSCODE)
  }

  return fetch(`${API_BASE_URL}${path}`, { ...init, headers })
}
