# Imaginea de bază
FROM node:18-alpine AS base

# Etapa 1: Instalarea dependențelor
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Etapa 2: Build-ul aplicației
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Dezactivăm colectarea de date anonime în timpul build-ului
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Etapa 3: Imaginea finală de rulare (Runner)
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Securitate: Rulăm aplicația ca utilizator non-root
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copiem doar fișierele strict necesare generate de build-ul standalone
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]