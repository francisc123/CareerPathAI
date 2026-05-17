.PHONY: help up down restart logs ps build clean clean-deep \
        keys redpanda-topics minio-init wait-healthy \
        logs-gateway logs-cv logs-agents logs-interview \
        test-flow1 test-flow2 smoke prod-up k8s-apply

# ─── Dev ───────────────────────────────────────────────────────────────────────
# Profiles are no longer used: a plain `docker compose up` starts the full stack.
up:
	@echo "→ Starting the full CareerPath AI stack (this can take a few minutes)…"
	docker compose up -d --build
	@$(MAKE) wait-healthy
	@echo ""
	@echo "✅ Stack is up. Open:"
	@echo "   Frontend          http://localhost:3000"
	@echo "   API Gateway       http://localhost:8000/health"
	@echo "   Keycloak          http://localhost:8484  (admin / admin)"
	@echo "   Redpanda Console  http://localhost:8080"
	@echo "   Grafana           http://localhost:3001  (admin / admin)"
	@echo "   MailHog           http://localhost:8025"

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

# Polls `docker compose ps` until every service reports healthy or 5 min pass.
# This is the gate that converts "containers started" into "stack is usable".
wait-healthy:
	@echo "→ Waiting for all services to report healthy (max 5 min)…"
	@bash -c '\
		end=$$(( $$(date +%s) + 300 )); \
		while [ $$(date +%s) -lt $$end ]; do \
			unhealthy=$$(docker compose ps --format json 2>/dev/null | \
				grep -E "\"Health\":\"(starting|unhealthy)\"" | wc -l | tr -d " "); \
			no_health=$$(docker compose ps --format json 2>/dev/null | \
				grep -v "\"Health\":" | grep "\"State\":\"running\"" | wc -l | tr -d " "); \
			if [ "$$unhealthy" = "0" ]; then \
				echo "   All services with healthchecks are healthy."; \
				exit 0; \
			fi; \
			echo "   …still waiting ($$unhealthy not healthy yet)"; \
			sleep 5; \
		done; \
		echo "⚠️  Timed out waiting for health. Run \"make ps\" to inspect."; \
		exit 1'

# ─── Database ──────────────────────────────────────────────────────────────────
# NOTE: Postgres initialises its schema automatically on first start by running
# every *.sql in /docker-entrypoint-initdb.d (mounted from infrastructure/postgres/init).
# A manual `make migrate` is therefore unnecessary for a fresh cold start.
# The target below exists only to re-apply the init scripts against an EXISTING
# database (e.g. after schema changes). It is destructive: it drops and recreates
# the schema, so it asks for confirmation.
migrate:
	@echo "⚠️  This will DROP and re-create the schema in the running Postgres."
	@echo "    Data will be lost. Press Ctrl+C to abort, Enter to continue."
	@read _
	@for f in infrastructure/postgres/init/*.sql; do \
		echo "→ Applying $$f"; \
		docker compose exec -T postgres psql \
			-U $${POSTGRES_USER:-cp_user} \
			-d $${POSTGRES_DB:-careerpath} \
			-v ON_ERROR_STOP=1 -f - < $$f; \
	done
	@echo "✓ Schema applied."

db-psql:
	docker compose exec postgres psql \
		-U $${POSTGRES_USER:-cp_user} \
		-d $${POSTGRES_DB:-careerpath}

# ─── Keys ──────────────────────────────────────────────────────────────────────
keys:
	@mkdir -p keys
	@if [ -f keys/private.pem ]; then \
		echo "✓ keys/private.pem already exists, skipping."; \
	else \
		openssl genrsa -out keys/private.pem 2048; \
		openssl rsa -in keys/private.pem -pubout -out keys/public.pem; \
		echo "✓ RS256 key pair generated in ./keys/"; \
	fi

# ─── Redpanda topics ───────────────────────────────────────────────────────────
# The container is named `cp-redpanda` (see docker-compose.yml).
redpanda-topics:
	docker cp infrastructure/redpanda/create-topics.sh cp-redpanda:/tmp/create-topics.sh
	docker exec cp-redpanda bash /tmp/create-topics.sh

# ─── MinIO Init ────────────────────────────────────────────────────────────────
minio-init:
	docker compose cp infrastructure/minio/init-buckets.sh minio:/tmp/init-buckets.sh
	docker compose exec minio bash /tmp/init-buckets.sh

# ─── Individual service logs ───────────────────────────────────────────────────
logs-gateway:
	docker compose logs -f api-gateway

logs-cv:
	docker compose logs -f cv-service cv-analyzer-agent

logs-agents:
	docker compose logs -f agent-orchestrator cv-analyzer-agent learning-path-agent job-match-agent

logs-interview:
	docker compose logs -f hr-interview-agent technical-interview-agent

# ─── E2E Testing ───────────────────────────────────────────────────────────────
test-flow1:
	@echo "Executing E2E Integration Test for Flow 1 (Python, cross-platform)..."
	@python tests/e2e/flow1_test.py

test-flow2:
	@echo "Checking E2E prerequisites for Flow 2…"
	@command -v jq >/dev/null 2>&1 || { echo >&2 "Error: 'jq' is required. Run: brew install jq"; exit 1; }
	@bash tests/e2e/flow2_test.sh

# Runs both flows back-to-back: the cold-start success criterion.
smoke: test-flow1 test-flow2
	@echo "✅ Both E2E flows passed."

# ─── Cleanup ───────────────────────────────────────────────────────────────────
# `clean` resets data but keeps built images, so the next `make up` is fast (~2-3 min).
clean:
	docker compose down -v --remove-orphans
	docker system prune -f
	@echo "✓ Containers and volumes removed. Built images kept."

# `clean-deep` simulates a fresh-machine cold start by also removing all images
# built locally for this project. The next `make up` will rebuild everything
# from scratch (~10-15 min on a Mac M-series with reasonable broadband).
clean-deep: clean
	@echo "→ Removing locally-built images for this project…"
	@docker images --format '{{.Repository}}:{{.Tag}}' \
		| grep -E '^careerpath-ai-' \
		| xargs -r docker rmi -f
	@echo "✓ Full clean complete. Next \`make up\` will rebuild from scratch."

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
	@echo "CareerPath AI — common commands"
	@echo ""
	@echo "  make keys             Generate the RS256 JWT key pair (idempotent)"
	@echo "  make up               Build and start the full stack, then wait for health"
	@echo "  make redpanda-topics  Create all Kafka topics (run once after first \`make up\`)"
	@echo "  make smoke            Run both E2E flows end-to-end"
	@echo ""
	@echo "  make test-flow1       Run Flow 1 (CV upload → analyze → match) E2E test"
	@echo "  make test-flow2       Run Flow 2 E2E test"
	@echo "  make test-flow3       Run Flow 3 (HR + Tech interview) E2E test"
	@echo ""
	@echo "  make ps               Show service status with health"
	@echo "  make logs             Tail all logs"
	@echo "  make logs-gateway     Tail just the API gateway"
	@echo "  make db-psql          Open psql in the running Postgres"
	@echo ""
	@echo "  make down             Stop everything (data preserved)"
	@echo "  make clean            Stop + delete volumes (data lost, images kept)"
	@echo "  make clean-deep       Same as clean + delete project images (slow next \`make up\`)"
	@echo ""
	@echo "  make migrate          Re-apply schema to an existing DB (destructive)"
	@echo "  make prod-up          Start in production mode"
