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