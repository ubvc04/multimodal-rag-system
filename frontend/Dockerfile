FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* /app/
RUN npm install
COPY . /app
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist /app/dist
RUN npm install -g serve
EXPOSE 5173
CMD ["serve", "-s", "/app/dist", "-l", "5173"]
