#!/bin/sh
HEADER='{"alg":"RS256","typ":"JWT"}'
IAT=$(date +%s)
EXP=$((IAT + 3600))
PAYLOAD="{\"sub\":\"test-user\",\"iss\":\"careerpath-ai-test\",\"iat\":${IAT},\"exp\":${EXP}}"
HEADER_B64=$(printf '%s' "$HEADER" | openssl base64 | tr -d '\n' | tr '+/' '-_' | tr -d '=')
PAYLOAD_B64=$(printf '%s' "$PAYLOAD" | openssl base64 | tr -d '\n' | tr '+/' '-_' | tr -d '=')
SIGNING_INPUT="${HEADER_B64}.${PAYLOAD_B64}"
SIG=$(printf '%s' "$SIGNING_INPUT" | openssl dgst -sha256 -sign ./keys/private.pem | openssl base64 | tr -d '\n' | tr '+/' '-_' | tr -d '=')
printf '%s.%s\n' "$SIGNING_INPUT" "$SIG"

