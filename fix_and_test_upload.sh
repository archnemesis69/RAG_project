#!/usr/bin/env bash
#
# fix_and_test_upload.sh
#
# 1. Adds DATA_DIR=/app/data to the rag-fastapi service in docker-compose.yml
#    (only if it's not already there).
# 2. Rebuilds and restarts rag-fastapi.
# 3. Uploads the given PDF directly to FastAPI's /documents endpoint
#    (bypassing the Spring Boot backend) so we see the REAL error message,
#    not just a generic "FAILED" status.
#
# Usage:
#   ./fix_and_test_upload.sh /path/to/your.pdf
#
set -uo pipefail

PDF_PATH="${1:-}"
COMPOSE_FILE="docker-compose.yml"
FASTAPI_URL="http://localhost:8000"

if [[ -z "$PDF_PATH" ]]; then
  echo "Usage: $0 /path/to/file.pdf"
  exit 1
fi

if [[ ! -f "$PDF_PATH" ]]; then
  echo "File not found: $PDF_PATH"
  exit 1
fi

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Run this from the repo root (where docker-compose.yml lives)."
  exit 1
fi

echo "==> Checking if DATA_DIR is already set for rag-fastapi..."
if grep -q "DATA_DIR=/app/data" "$COMPOSE_FILE"; then
  echo "    Already present. Skipping edit."
else
  echo "    Not found — adding it."
  cp "$COMPOSE_FILE" "${COMPOSE_FILE}.bak"

  # Insert "- DATA_DIR=/app/data" right after the OLLAMA_HOST line
  # inside the rag-fastapi service's environment block.
  awk '
    { print }
    /OLLAMA_HOST=http:\/\/host.docker.internal:11434/ && !done {
      print "      - DATA_DIR=/app/data"
      done = 1
    }
  ' "${COMPOSE_FILE}.bak" > "$COMPOSE_FILE"

  if grep -q "DATA_DIR=/app/data" "$COMPOSE_FILE"; then
    echo "    Added successfully. Backup saved as ${COMPOSE_FILE}.bak"
  else
    echo "    Could not auto-insert (OLLAMA_HOST line not found in expected format)."
    echo "    Please add this line manually under rag-fastapi's 'environment:' block:"
    echo "      - DATA_DIR=/app/data"
    mv "${COMPOSE_FILE}.bak" "$COMPOSE_FILE"
  fi
fi

echo
echo "==> Rebuilding and restarting rag-fastapi..."
docker compose up --build -d rag-fastapi

echo "==> Waiting a few seconds for the service to come up..."
sleep 5

echo
echo "==> Confirming DATA_DIR resolves correctly inside the container..."
docker compose exec rag-fastapi python3 -c "import os; os.chdir('/app'); print('DATA_DIR resolves to:', os.path.abspath(os.environ.get('DATA_DIR', '../data')))"

echo
echo "==> Uploading PDF directly to FastAPI (bypassing the Java backend)..."
FILESIZE=$(du -h "$PDF_PATH" | cut -f1)
echo "    File: $PDF_PATH ($FILESIZE)"

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$FASTAPI_URL/documents" \
  -F "file=@${PDF_PATH}" \
  -F "owner_id=default")

BODY=$(echo "$RESPONSE" | sed -n '1,/HTTP_STATUS:/p' | sed '$d')
STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)

echo
echo "==> HTTP Status: $STATUS"
echo "==> Response body:"
echo "$BODY" | jq . 2>/dev/null || echo "$BODY"

echo
echo "==> Recent rag-fastapi logs (for extra context):"
docker compose logs --tail=30 rag-fastapi

echo
echo "==> Done."
