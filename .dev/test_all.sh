#!/usr/bin/env bash
# Roda todas as baterias de teste (Playwright) contra a prévia. Rodar de dentro de .dev/ (os testes salvam prints em t2/).
cd "$(dirname "$0")"
python3 build_painel.py >/dev/null; bash serve.sh
for t in tests/tinvite.py tests/tajustes.py tests/t4run.py tests/t3run.py tests/tverify.py tests/t6.py tests/tcsp.py tests/tblink.py tests/ttodos.py tests/tmerc.py tests/tswipe.py tests/tpres.py tests/tnovas.py tests/tinicio.py tests/tpainel.py; do
  echo "== $t"; timeout 590 python3 "$t" 2>&1 | grep -E "^FAIL|FAILS|NO ERR|NO PAGE|rror:|Traceback" | head -5
done
echo "== tests/tcrawl.py (só erro de fonte bloqueada é esperado)"; timeout 400 python3 tests/tcrawl.py 2>&1 | grep -v TUNNEL | tail -2
