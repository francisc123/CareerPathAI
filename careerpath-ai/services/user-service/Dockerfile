# User Service — NestJS + Prisma ORM
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npx prisma generate
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 appuser
COPY --from=builder --chown=appuser:nodejs /app/dist           ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules   ./node_modules
COPY --from=builder /app/package.json ./
USER appuser
EXPOSE 8001
CMD ["node", "dist/main.js"]
