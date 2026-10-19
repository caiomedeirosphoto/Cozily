#!/usr/bin/env bash
# Confere a sintaxe do index.html e monta a prévia (modo demonstração) em .dev/t2/
#   .dev/t2/cozily.html  -> publicar como artifact de prévia
#   .dev/t2/index.html   -> usado pelos testes (servido em http://localhost:8811)
set -e
cd "$(dirname "$0")/.."
python3 -c "
import re
h=open('index.html').read()
m=re.findall(r'<script type=\"module\">(.*?)</script>',h,re.S); open('.dev/t2/check.mjs','w').write(m[0])" 2>/dev/null || { mkdir -p .dev/t2; python3 -c "
import re
h=open('index.html').read()
m=re.findall(r'<script type=\"module\">(.*?)</script>',h,re.S); open('.dev/t2/check.mjs','w').write(m[0])"; }
node --check .dev/t2/check.mjs
python3 .dev/build_preview.py >/dev/null
(printf '<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">\n'; cat .dev/t2/cozily.html) > .dev/t2/index.html
# cópia com a política de segurança (CSP) do app real, pro teste tests/tcsp.py
python3 -c "
import re
csp=re.search(r'<meta http-equiv=\"Content-Security-Policy\"[^>]*>',open('index.html').read()).group(0)
open('.dev/t2/csp.html','w').write(csp+open('.dev/t2/index.html').read())"
echo BUILD_OK
