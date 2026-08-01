#!/usr/bin/env bash
#
# make_it_work.sh
#
# Full diagnosis + fix for the Docker-bridge-can't-reach-Ollama problem,
# then an end-to-end verification of the whole RAG stack.
#
# Usage:
#   ./make_it_work.sh
#
set -uo pipefail
PASS="✅"
FAIL="❌"

echo "=================================================="
echo "STEP 0 — Baseline checks"
echo "=================================================="

echo
echo "-- Is Ollama running and correctly bound? --"
if ss -tlnp 2>/dev/null | grep -q "11434"; then
  ss -tlnp | grep 11434
else
  echo "$FAIL Ollama not listening at all. Starting it..."
  pkill -f "ollama serve" 2>/dev/null
  sleep 2
  OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama_serve.log 2>&1 &
  sleep 3
  ss -tlnp | grep 11434 || echo "$FAIL Still not up — check /tmp/ollama_serve.log"
fi

echo
echo "-- Can the HOST reach Ollama via the Docker bridge IP? --"
BRIDGE_IP=$(ip -4 addr show docker0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
echo "    Docker bridge IP: ${BRIDGE_IP:-not found}"
if [[ -n "${BRIDGE_IP:-}" ]]; then
  if curl -s --max-time 3 "http://${BRIDGE_IP}:11434" | grep -q "running"; then
    echo "$PASS Host can reach Ollama via bridge IP."
    BRIDGE_OK=1
  else
    echo "$FAIL Host CANNOT reach Ollama via bridge IP — this is the real problem."
    BRIDGE_OK=0
  fi
else
  echo "$FAIL docker0 interface not found."
  BRIDGE_OK=0
fi

if [[ "${BRIDGE_OK:-0}" == "1" ]]; then
  echo
  echo "Bridge connectivity is fine — the earlier failure may have been transient"
  echo "or container-specific. Skipping firewall changes, jumping to Docker checks."
else
  echo
  echo "=================================================="
  echo "STEP 1 — Identify the actual firewall backend"
  echo "=================================================="

  echo
  echo "-- nftables ruleset (if any) --"
  NFT_OUTPUT=$(sudo nft list ruleset 2>/dev/null)
  if [[ -n "$NFT_OUTPUT" ]]; then
    echo "$NFT_OUTPUT" | head -80
    USING_NFT=1
  else
    echo "    (empty or nft not in use)"
    USING_NFT=0
  fi

  echo
  echo "-- iptables ruleset (legacy or nft-backed) --"
  sudo iptables -L -n -v --line-numbers

  echo
  echo "-- Active firewall-management services --"
  sudo systemctl list-units --type=service --state=running 2>/dev/null | grep -i -E "firewall|nft" || echo "    None found running as a service."

  echo
  echo "-- Docker daemon config (checking for leftover MTU/network tweaks) --"
  if [[ -f /etc/docker/daemon.json ]]; then
    cat /etc/docker/daemon.json
  else
    echo "    No /etc/docker/daemon.json found."
  fi

  echo
  echo "=================================================="
  echo "STEP 2 — Apply targeted fix"
  echo "=================================================="

  if [[ "$USING_NFT" == "1" ]]; then
    echo "    nftables is in use. Adding an accept rule for the docker0 bridge..."
    sudo nft insert rule inet filter forward iifname "docker0" accept 2>/dev/null
    sudo nft insert rule inet filter forward oifname "docker0" accept 2>/dev/null
    sudo nft insert rule inet filter input iifname "docker0" accept 2>/dev/null
    echo "    (If this printed errors, the table/chain names differ from 'inet filter' —"
    echo "     see the ruleset dump above for the real chain names and I'll give you"
    echo "     the exact command.)"
  else
    echo "    Using iptables-style rules. Inserting explicit ACCEPT rules for docker0..."
    sudo iptables -I FORWARD 1 -i docker0 -j ACCEPT
    sudo iptables -I FORWARD 1 -o docker0 -j ACCEPT
    sudo iptables -I INPUT 1 -i docker0 -j ACCEPT
  fi

  echo
  echo "-- Restarting Docker to reassert its own chains cleanly on top --"
  sudo systemctl restart docker
  sleep 3

  echo
  echo "-- Re-testing host -> bridge IP --"
  BRIDGE_IP=$(ip -4 addr show docker0 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}')
  if curl -s --max-time 3 "http://${BRIDGE_IP}:11434" | grep -q "running"; then
    echo "$PASS Fixed — host can now reach Ollama via bridge IP."
  else
    echo "$FAIL Still blocked. This needs manual inspection of the ruleset above."
    echo "    Paste the STEP 1 output back and we'll pinpoint the exact rule."
  fi
fi

echo
echo "=================================================="
echo "STEP 3 — Bring the full stack up and verify"
echo "=================================================="

docker compose up --build -d
sleep 8
docker compose ps

echo
echo "-- rag-fastapi -> Ollama (from inside the container) --"
docker compose exec -T rag-fastapi python3 -c "
import urllib.request
try:
    print('PASS:', urllib.request.urlopen('http://host.docker.internal:11434', timeout=5).read())
except Exception as e:
    print('FAIL:', e)
"

echo
echo "-- FastAPI health --"
curl -s http://localhost:8000/health && echo

echo
echo "-- Real ingestion test --"
if [[ -f /home/azizk/Downloads/1.pdf ]]; then
  curl -s -X POST http://localhost:8000/documents \
    -F "file=@/home/azizk/Downloads/1.pdf" \
    -F "owner_id=default" | jq . 2>/dev/null
else
  echo "    (1.pdf not found at expected path, skipping — test manually)"
fi

echo
echo "-- Real query test --"
curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "what is this document about", "top_k": 3, "owner_id": "default"}' \
  | jq . 2>/dev/null

echo
echo "=================================================="
echo "Done. If STEP 3's ingestion/query tests show real"
echo "content (not connection errors), the stack is fully working."
echo "=================================================="
