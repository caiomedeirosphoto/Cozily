import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(ROOT,'.dev','t2'),exist_ok=True)
import re
src=open(os.path.join(ROOT,'index.html'),encoding='utf-8').read()
src=re.sub(r'apiKey: "[^"]*"','apiKey: "COLE_AQUI"',src)
title=re.search(r'<title>.*?</title>',src).group(0)
fonts=re.search(r'<link rel="stylesheet" href="https://fonts.googleapis.com[^>]*>',src).group(0)
style=re.search(r'<style>(.*?)</style>',src,re.S).group(1)
body=re.search(r'<body>(.*)</body>',src,re.S).group(1)

# dark blocks -> guarded + data-theme copies
def transform(css):
    out=[];i=0;key='@media (prefers-color-scheme: dark){'
    while True:
        j=css.find(key,i)
        if j<0: out.append(css[i:]);break
        out.append(css[i:j]); k=j+len(key); depth=1; m=k
        while depth:
            if css[m]=='{':depth+=1
            elif css[m]=='}':depth-=1
            m+=1
        inner=css[k:m-1]
        def pref(p):
            res=[]
            for rule in re.finditer(r'([^{}]+)\{([^{}]*)\}',inner):
                sels=[s.strip() for s in rule.group(1).split(',')]
                ns=[(p if s==':root' else p+' '+s) for s in sels]
                res.append(','.join(ns)+'{'+rule.group(2)+'}')
            return '\n'.join(res)
        out.append(key+pref(':root:not([data-theme="light"])')+'}\n'+pref(':root[data-theme="dark"]'))
        i=m
    return ''.join(out)
# source already handles data-theme
style=style.replace('--top:env(safe-area-inset-top,0px);','--top:0px;')
style+='\nbody{background:var(--bg)}\n'
def must(a,b):
    global body
    assert a in body, a[:60]
    body=body.replace(a,b)
must('const DEMO_PRELOAD = false;','const DEMO_PRELOAD = true;')
must('value="${esc(S.authEmail || "")}"','value="${esc(S.authEmail || (criar ? "" : "caio@exemplo.com"))}"')
must('<input class="input" id="lSenha" type="password"','<input class="input" id="lSenha" ${criar ? "" : \'value="demonstracao"\'} type="password"')
must('${row("data-go=dados", "dl", "Baixar meus dados", "Cópia de tudo, num arquivo")}','')
must('<button class="btn ghost block" type="button" data-dados>${ic("dl", 18, 2)} Antes, baixar meus dados</button>','')
must('$("[data-dados]", ov).onclick = baixarDados;','')
must('const KEY = "cozily-demo-v3";','const KEY = "cozily-preview-v6";')
open(os.path.join(ROOT,'.dev','t2','cozily.html'),'w',encoding='utf-8').write(title+'\n'+fonts+'\n<style>'+style+'</style>\n'+body)
print(style.count('data-theme="dark"'), style.count('data-theme="light"'))
