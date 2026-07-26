import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ mode }) => {
  // loadEnv は .env ファイルに加えて、VITE_ で始まる実際の環境変数も拾う。
  // Vercel は環境変数として渡してくるので、この形でないと検出できない。
  const env = loadEnv(mode, process.cwd(), 'VITE_')
  const apiBaseUrl = env.VITE_API_BASE_URL ?? process.env.VITE_API_BASE_URL

  // 本番ビルドで未設定なら、ここで落とす。
  // ランタイムに throw してもビルドは通ってしまい、デプロイ後に初めて壊れるため。
  if (mode === 'production' && !apiBaseUrl) {
    throw new Error(
      'VITE_API_BASE_URL が未設定です。本番ビルドには必須です。\n' +
        'Vercel では Project Settings > Environment Variables に設定してください。\n' +
        'ローカルで本番ビルドを試す場合は frontend/.env.production に記述します。',
    )
  }

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    build: {
      // minify を無効化（KaTeXのレンダリング問題対策）
      minify: false,
    },
  }
})
