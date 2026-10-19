#!/usr/bin/env bash
# Sobe um servidor local da prévia na porta 8811 (os testes usam ele). Rode antes de cada bateria de testes.
cd "$(dirname "$0")/t2"
curl -s -o /dev/null http://localhost:8811/index.html && exit 0
nohup setsid python3 -m http.server 8811 >/dev/null 2>&1 < /dev/null &
disown; sleep 1.2
