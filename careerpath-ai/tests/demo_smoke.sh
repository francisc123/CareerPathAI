#!/usr/bin/env bash
# Pre-demo smoke check — rulat cu `bash tests/demo_smoke.sh` din careerpath-ai/
# Verifica: toate containerele up, health-uri OK, frontend reachable,
# Kafka stable, chat agent ok.
# Iesire 0 = demo-ready. Orice cod != 0 = fix inainte de demo.

set -u
PASS=0; FAIL=0
ok()  { echo "  [OK]   $1"; PASS=$((PASS+1)); }
bad() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }

echo "== 1. Containere =="
for c in cp-orchestrator cp-cv-analyzer cp-learning-agent cp-job-match cp-hr-agent cp-tech-agent \
         cp-cv-service cp-frontend cp-postgres cp-redis cp-redpanda cp-minio cp-qdrant; do
  s=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo "missing")
  if [ "$s" = "running" ]; then ok "$c running"; else bad "$c = $s"; fi
done

echo
echo "== 2. Health endpoints =="
for p in 8002:cv-service 8005:orchestrator 8006:cv-analyzer 8007:learning 8008:job-match 8009:hr 8010:tech 3000:frontend; do
  port="${p%%:*}"; name="${p##*:}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:$port/health" 2>/dev/null || true)
  if [ "$port" = "3000" ]; then
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://localhost:$port" 2>/dev/null || true)
  fi
  if [ "$code" = "200" ] || [ "$code" = "404" ]; then ok "$name (HTTP $code)"; else bad "$name (HTTP $code)"; fi
done

echo
echo "== 3. cv-analyzer dependencies (Gemini, Kafka, DB, Qdrant) =="
detail=$(curl -s --max-time 5 http://localhost:8006/health)
echo "  $detail"
echo "$detail" | grep -q '"gemini_api_key":"ok"' && ok "Gemini OK" || bad "Gemini check"
echo "$detail" | grep -q '"kafka_producer":"ok"' && ok "Kafka OK" || bad "Kafka check"
echo "$detail" | grep -q '"qdrant":"ok"' && ok "Qdrant OK" || bad "Qdrant check"

echo
echo "== 4. Kafka consumer groups =="
dead=$(docker exec cp-redpanda rpk group list 2>/dev/null | awk 'NR>1 && $3=="Dead"' | wc -l)
if [ "$dead" = "0" ]; then ok "Niciun consumer group Dead"; else bad "$dead consumer groups Dead"; fi

echo
echo "== 5. Chat agent (greeting fix la __init__) =="
if PYTHONIOENCODING=utf-8 python -c "
import asyncio, json, uuid, websockets, sys
async def t():
  uid = f'smoke-{uuid.uuid4().hex[:6]}'
  async with websockets.connect(f'ws://localhost:8005/ws/chat/{uid}') as ws:
    while True:
      r = json.loads(await asyncio.wait_for(ws.recv(), timeout=15))
      if r.get('type') == 'message':
        sys.exit(0 if 'Bun venit' in r.get('text','') else 1)
asyncio.run(t())
" 2>/dev/null; then ok "Chat greeting OK"; else bad "Chat greeting failed"; fi

echo
echo "============================="
echo "  Total: $PASS OK, $FAIL FAIL"
echo "============================="
[ "$FAIL" = "0" ] && exit 0 || exit 1
