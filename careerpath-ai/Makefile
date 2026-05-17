.PHONY: up down logs ps build clean migrate keys help

# ─── Dev ───────────────────────────────────────────────────────────────────────
up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose down && docker compose up -d --build

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

build:
	docker compose build --no-cache

# ─── Database ──────────────────────────────────────────────────────────────────
migrate:
	docker compose exec user-service npx prisma migrate dev

migrate-prod:
	docker compose exec user-service npx prisma migrate deploy

db-studio:
	docker compose exec user-service npx prisma studio

# ─── Keys ──────────────────────────────────────────────────────────────────────
keys:
	mkdir -p keys
	openssl genrsa -out keys/private.pem 2048
	openssl rsa -in keys/private.pem -pubout -out keys/public.pem
	@echo "✓ RS256 key pair generated in ./keys/"

# ─── Kafka topics ──────────────────────────────────────────────────────────────
# ─── Redpanda topics ───────────────────────────────────────────────────────────
# ─── Redpanda topics ───────────────────────────────────────────────────────────
redpanda-topics:
	docker cp infrastructure/redpanda/create-topics.sh careerpath-ai-redpanda-1:/tmp/create-topics.sh
	docker exec careerpath-ai-redpanda-1 bash /tmp/create-topics.sh

# ─── Individual service logs ───────────────────────────────────────────────────
logs-gateway:
	docker compose logs -f api-gateway

# ─── MinIO Init ────────────────────────────────────────────────────────────────
minio-init:
	docker-compose cp infrastructure/minio/init-buckets.sh minio:/tmp/init-buckets.sh
	docker-compose exec minio bash /tmp/init-buckets.sh

logs-cv:
	docker compose logs -f cv-service cv-analyzer-agent

logs-agents:
	docker compose logs -f agent-orchestrator cv-analyzer-agent learning-path-agent job-match-agent

logs-interview:
	docker compose logs -f hr-interview-agent technical-interview-agent

# ─── Cleanup ───────────────────────────────────────────────────────────────────
clean:
	docker compose down -v --remove-orphans
	docker system prune -f

# ─── Production ────────────────────────────────────────────────────────────────
prod-up:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

k8s-apply:
	kubectl apply -f k8s/namespaces/
	kubectl apply -f k8s/configmaps/
	kubectl apply -f k8s/secrets/
	kubectl apply -f k8s/deployments/
	kubectl apply -f k8s/services/
	kubectl apply -f k8s/ingress/
	kubectl apply -f k8s/hpa/

# ─── E2E tests ─────────────────────────────────────────────────────────────────
test-flow3:
	@echo "Running Flow 3 (HR + Tech interview) e2e test..."
	@python tests/e2e/flow3_test.py

help:
	@echo "Available commands:"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make logs         - Tail all logs"
	@echo "  make migrate      - Run DB migrations"
	@echo "  make keys         - Generate RS256 JWT keys"
	@echo "  make kafka-topics - Create Kafka topics"
	@echo "  make clean        - Remove all containers and volumes"
	@echo "  make prod-up      - Start in production mode"
	@echo "  make test-flow3   - Run Flow 3 (HR + Tech interview) e2e test"
