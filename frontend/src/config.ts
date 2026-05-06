// API のベース URL を環境変数から取得する
// 開発時：vite の起動時に frontend/.env の VITE_API_BASE_URL が読まれる
// 本番時：ビルド時に frontend/.env.production の VITE_API_BASE_URL が読まれる
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL