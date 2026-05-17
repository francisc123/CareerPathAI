#!/usr/bin/env bash
# Creates every Kafka topic CareerPath AI needs. Idempotent — re-running it is safe.
set -euo pipefail

TOPICS=(
  cv.uploaded
  cv.analyzed
  gaps.identified
  learning.path.created
  learning.completed
  jobs.matched
  interview.hr.completed
  interview.tech.completed
  orchestrator.dlq
)

PARTITIONS="${KAFKA_TOPIC_PARTITIONS:-1}"
REPLICAS="${KAFKA_TOPIC_REPLICAS:-1}"

echo "→ Creating ${#TOPICS[@]} topics (partitions=$PARTITIONS, replicas=$REPLICAS)…"

for topic in "${TOPICS[@]}"; do
  if rpk topic create "$topic" -p "$PARTITIONS" -r "$REPLICAS" 2>/dev/null; then
    echo "   created  $topic"
  else
    # The most common failure here is "already exists", which is fine.
    if rpk topic list | grep -q "^${topic}\b"; then
      echo "   exists   $topic"
    else
      echo "   ❌ failed $topic" >&2
      exit 1
    fi
  fi
done

echo ""
echo "✓ Topics ready:"
rpk topic list