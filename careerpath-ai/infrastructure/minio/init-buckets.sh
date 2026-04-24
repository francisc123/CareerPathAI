#!/bin/bash
# MinIO bucket initialization — runs once after MinIO starts

#am modificat parametrii ca sa se potriveasca cu cei din docker-compose ~Francisc
mc alias set local http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD"

mc mb --ignore-existing local/cvs-raw
mc mb --ignore-existing local/cvs-processed
mc mb --ignore-existing local/course-materials

# Lifecycle: delete raw CVs after 90 days (GDPR)
mc ilm rule add --expiry-days 90 local/cvs-raw

# Versioning on processed CVs
mc version enable local/cvs-processed

echo "MinIO buckets initialized."