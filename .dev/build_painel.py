# Monta a prévia do painel (modo demonstração) em .dev/t2/painel.html
import os,re
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s=open(os.path.join(ROOT,'painel','index.html'),encoding='utf-8').read()
s=re.sub(r'apiKey: "[^"]*"','apiKey: "COLE_AQUI"',s,count=1)
os.makedirs(os.path.join(ROOT,'.dev','t2'),exist_ok=True)
open(os.path.join(ROOT,'.dev','t2','painel.html'),'w',encoding='utf-8').write(s)
m=re.search(r'<script type="module">(.*?)</script>',s,re.S).group(1)
open(os.path.join(ROOT,'.dev','t2','painel-check.mjs'),'w').write(m)
print('PAINEL_OK')
# versão para o artifact de teste: sem doctype/html/head/body (o artifact põe o esqueleto) e sem a CSP do site
a=re.sub(r'<meta http-equiv="Content-Security-Policy"[^>]*>\n?','',s)
a=re.sub(r'<!doctype html>\s*<html[^>]*>\s*<head>\s*','',a)
a=a.replace('</head>\n<body>\n','').replace('</body>\n</html>\n','')
a=re.sub(r'<meta charset="utf-8">\n<meta name="viewport"[^>]*>\n','',a)
open(os.path.join(ROOT,'.dev','t2','painel-artifact.html'),'w',encoding='utf-8').write(a)
