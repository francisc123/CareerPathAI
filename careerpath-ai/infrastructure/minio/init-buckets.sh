#!/bin/bash
# MinIO bucket initialization — runs once after MinIO starts

mc alias set local http://minio:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY"

mc mb --ignore-existing local/cvs-raw
mc mb --ignore-existing local/cvs-processed
mc mb --ignore-existing local/course-materials

# Lifecycle: delete raw CVs after 90 days (GDPR)
mc ilm rule add --expiry-days 90 local/cvs-raw

# Versioning on processed CVs
mc version enable local/cvs-processed

echo "MinIO buckets initialized."
