# これは docker compose（開発環境）専用。
# 本番のフロントエンドは Vercel が直接ビルド・配信するので、この Dockerfile は使わない。
# 手順は docs/deploy.md を参照。
FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# 本番用にビルド
RUN npm run build

EXPOSE 5173

# preview サーバーで配信
CMD ["npm", "run", "preview"]