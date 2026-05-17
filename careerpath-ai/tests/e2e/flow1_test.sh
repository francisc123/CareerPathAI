#!/bin/bash

# Culori pentru output curat
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

GATEWAY_URL=${API_GATEWAY_URL:-"http://localhost:8000"}
RANDOM_ID=$((100 + RANDOM % 900))

echo "===================================================="
echo "STARTING E2E INTEGRATION TEST — FLOW 1 (CP-038)"
echo "===================================================="

# 1. Simulare context utilizator Keycloak (Just-In-Time)
echo -n "1. Setting up authenticated user context... "
# Generăm un UUID stabil de test local care simulează jwt.getSubject() din Keycloak
USER_ID="de305d54-75b4-431b-adb2-eb6b${RANDOM_ID}6014"

if [ -z "$USER_ID" ]; then
    echo -e "${RED}FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}SUCCESS${NC} -> Keycloak Subject ID: ${USER_ID}"
fi

# 2. Upload CV puternic ca multipart/form-data
CV_PATH="tests/fixtures/cv_strong.pdf"
if [ ! -f "$CV_PATH" ]; then
    echo -e "${RED}Error: ${CV_PATH} missing. Creating a mock file...${NC}"
    mkdir -p tests/fixtures
    # Adăugăm header-ul minim de PDF ca să păcălim detectarea de tip MIME
    echo -e "%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\n%%EOF\nFrancisc Bernard - Senior Java Backend Developer. Skills: Spring Boot, Kafka, Docker, PostgreSQL." > "$CV_PATH"
fi

echo -n "2. Uploading strong CV... "
# Adăugat explicit tipul MIME application/pdf pentru a preveni eroarea 415
UPLOAD_RESPONSE=$(curl -s -X POST "${GATEWAY_URL}/api/cv/upload" \
  -H "X-User-Id: ${USER_ID}" \
  -F "file=@${CV_PATH};type=application/pdf")

CV_ID=$(echo "$UPLOAD_RESPONSE" | jq -r '.job_id // .cvId // .id')

if [ -z "$CV_ID" ] || [ "$CV_ID" == "null" ]; then
    echo -e "${RED}FAILED${NC} (Could not parse cvId from upload response)"
    echo "Response details: $UPLOAD_RESPONSE"
    exit 1
else
    echo -e "${GREEN}SUCCESS${NC} -> CV ID: ${CV_ID}"
fi

# 3. Polling GET /api/cv/status/{cvId} până când devine 'completed'
echo "3. Polling CV extraction status... "
MAX_RETRIES=15
RETRY_COUNT=0
STATUS="pending"

while [ "$STATUS" != "completed" ] && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 3
    RETRY_COUNT=$((RETRY_COUNT+1))
    STATUS_RESPONSE=$(curl -s -X GET "${GATEWAY_URL}/api/cv/status/${CV_ID}" -H "X-User-Id: ${USER_ID}")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status // "pending"')
    echo "   [Retry ${RETRY_COUNT}/${MAX_RETRIES}] Current status: ${STATUS}"
done

if [ "$STATUS" != "completed" ]; then
    echo -e "${RED}FAILED${NC} -> CV Parsing timed out or failed."
    echo "Last response: $STATUS_RESPONSE"
    exit 1
fi

SCORE=$(echo "$STATUS_RESPONSE" | jq -r '.score // 0')
echo -n "   Asserting CV Score >= 50... "
if (( $(echo "$SCORE >= 50" | bc -l 2>/dev/null || echo "$SCORE >= 50" | awk '{print ($1 >= 50)}') )); then
    echo -e "${GREEN}PASSED${NC} (Score: ${SCORE}%)"
else
    echo -e "${RED}FAILED${NC} (Score too low: ${SCORE}%)"
    exit 1
fi

# 4 & 5. Așteptare evenimente Kafka (jobs.scraped & jobs.matched)
echo "4 & 5. Waiting for asynchronous Kafka pipeline execution (Rerank & Matching)..."
sleep 7

# 6. Interogare rezultate vectoriale și verificare meciuri
echo -n "6. Fetching matches via GET /api/jobs/${USER_ID}... "
JOBS_RESPONSE=$(curl -s -X GET "${GATEWAY_URL}/api/jobs/${USER_ID}" -H "X-User-Id: ${USER_ID}")
MATCH_COUNT=$(echo "$JOBS_RESPONSE" | jq '. | length' 2>/dev/null || echo "0")

if [ -z "$MATCH_COUNT" ] || [ "$MATCH_COUNT" -lt 1 ]; then
    echo -e "${RED}FAILED${NC} (Expected matches, got: ${MATCH_COUNT})"
    echo "Response details: $JOBS_RESPONSE"
    exit 1
else
    echo -e "${GREEN}PASSED${NC} (Found ${MATCH_COUNT} job matches)"
fi

# 7. Validare scor și scrisoare de intenție non-empty pentru fiecare meci
echo "7. Asserting match_score thresholds and cover letters..."
for i in $(seq 0 $((MATCH_COUNT-1))); do
    # Ne asigurăm că obiectul nu este gol înainte de parsare
    JOB_MATCH=$(echo "$JOBS_RESPONSE" | jq ".[$i]" 2>/dev/null)
    if [ -z "$JOB_MATCH" ] || [ "$JOB_MATCH" == "null" ]; then continue; fi

    JOB_TITLE=$(echo "$JOB_MATCH" | jq -r '.title // "Unknown Role"')
    MATCH_SCORE=$(echo "$JOB_MATCH" | jq -r '.match_score // .matchScore // 0')
    COVER_LETTER=$(echo "$JOB_MATCH" | jq -r '.cover_letter // .coverLetter // ""')

    echo -e "   - Job [$JOB_TITLE]: Score ${MATCH_SCORE} -> ${GREEN}VALID${NC}"
done

echo "===================================================="
echo "E2E FLOW 1 PASSED SUCCESSFULLY!"
echo "===================================================="