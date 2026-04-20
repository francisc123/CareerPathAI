#!/bin/bash
# Run after Redpanda is healthy: make redpanda-topics

BROKER="redpanda:9092"
RETENTION="604800000"   # 7 days in ms
PARTITIONS=3
REPLICAS=1              # 1 for dev, 3 for prod

topics=(
  "user.registered"
  "cv.uploaded"
  "cv.analyzed"
  "gaps.identified"
  "jobs.scraped"
  "jobs.matched"
  "learning.path.created"
  "learning.completed"
  "interview.hr.completed"
  "interview.tech.completed"
)

for topic in "${topics[@]}"; do
  rpk topic create "$topic" \
    --brokers "$BROKER" \
    --partitions "$PARTITIONS" \
    --replicas "$REPLICAS" \
    --config retention.ms="$RETENTION"
  echo "Created topic: $topic"
done

echo "All topics created."
