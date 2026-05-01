# API Gateway — NestJS + Fastify adapter

# ── Development (hot reload) ───────────────────────────────────────────────────
FROM node:20-alpine AS dev
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
EXPOSE 8000
CMD ["npm", "run", "start:dev"]

# ── Builder (compilarea codului TypeScript) ────────────────────────────────────
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

# ── Production (imagine mica si securizata) ────────────────────────────────────
FROM node:20-alpine AS production
WORKDIR /app
ENV NODE_ENV=production
# Cream un user fara drepturi de root pentru securitate
RUN addgroup --system --gid 1001 nodejs \
 && adduser  --system --uid 1001 appuser
# Copiem doar codul compilat din etapa de builder
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY package.json ./
# Schimbam pe userul securizat
USER appuser
EXPOSE 8000
CMD ["node", "dist/main.js"]