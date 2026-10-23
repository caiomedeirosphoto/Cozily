# Pente fino: todas as telas e folhas, claro/escuro, 320/390. Checa erros, texto quebrado, vazamento,
# alvos de toque pequenos, contraste baixo e elementos sobrepostos. Salva prints em t4/audit.
import asyncio, json
from playwright.async_api import async_playwright
B='http://localhost:8811/index.html'
ROUTES=['#/','#/comodos','#/ordem','#/mercado','#/mercado/gastos','#/financas','#/presentes','#/avisos','#/achadinhos','#/atividade','#/busca','#/c/cozinha','#/c/quarto','#/c/banheiro','#/i/cozinha--eletrodomesticos--geladeira','#/i/banheiro--toalhas--toalhas-de-banho','#/l/caio-e-mirielly']
SHEETS=[('#/','[data-act=settings]'),('#/','.fab'),('#/financas','[data-act=guardar]'),('#/mercado','[data-act=m-month]'),('#/c/cozinha','[data-act=toggle]'),('#/i/cozinha--eletrodomesticos--geladeira','[data-act=edit]')]
CHECK=r"""()=>{
 const out=[]; const vis=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'};
 const root=document.querySelector('.overlay .sheet')||document.querySelector('#app');
 // alvos de toque
 root.querySelectorAll('button,a,[role=button],input,select').forEach(e=>{ if(!vis(e))return; const r=e.getBoundingClientRect(); if((r.height<32||r.width<32)&&!e.closest('.chips,.wrapchips,.meta,p,.priv')) out.push('toque pequeno: '+(e.getAttribute('aria-label')||e.textContent.trim().slice(0,30)||e.tagName)+' '+Math.round(r.width)+'x'+Math.round(r.height)); });
 // texto cortado
 root.querySelectorAll('*').forEach(e=>{ if(!vis(e)||e.children.length)return; const cs=getComputedStyle(e); if(e.scrollWidth>e.clientWidth+2&&cs.overflow!=='visible'&&cs.textOverflow!=='ellipsis'&&!e.closest('.chips,.carrossel,.photos,.chart,input,textarea')) out.push('cortado: '+e.textContent.trim().slice(0,40)); });
 // contraste
 const lum=c=>{const m=c.match(/[\d.]+/g);if(!m)return null;const [r,g,b,a=1]=m.map(Number);if(a<0.5)return null;return [r,g,b].map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0)};
 const bgOf=e=>{for(let x=e;x;x=x.parentElement){const c=getComputedStyle(x).backgroundColor;const l=lum(c);if(l!==null&&!/rgba\(\d+, \d+, \d+, 0\)/.test(c))return l;}return lum(getComputedStyle(document.body).backgroundColor)};
 root.querySelectorAll('*').forEach(e=>{ if(!vis(e))return; const t=[...e.childNodes].filter(n=>n.nodeType===3&&n.textContent.trim()).map(n=>n.textContent.trim()).join(' '); if(!t)return; const cs=getComputedStyle(e); if(cs.opacity<.9||e.closest('[disabled],s,.demo'))return; const f=lum(cs.color),bg=bgOf(e); if(f==null||bg==null)return; const cr=(Math.max(f,bg)+.05)/(Math.min(f,bg)+.05); const big=parseFloat(cs.fontSize)>=18.5||(parseFloat(cs.fontSize)>=14&&+cs.fontWeight>=700); if(cr<(big?3:4.5)) out.push('contraste '+cr.toFixed(2)+': '+t.slice(0,35)); });
 // texto ruim
 const tx=root.innerText; ['undefined','NaN','null','[object','Infinity'].forEach(b=>{ if(new RegExp('\\b'+b.replace('[','\\[')+'\\b').test(tx)) out.push('texto ruim: '+b) });
 if(document.documentElement.scrollWidth>innerWidth+1) out.push('rolagem lateral');
 return [...new Set(out)].slice(0,25);
}"""
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); rep={}
    for w in [320,390]:
      for s in ['light','dark']:
        ctx=await b.new_context(viewport={'width':w,'height':800},color_scheme=s,device_scale_factor=1)
        pg=await ctx.new_page(); errs=[]
        pg.on('pageerror',lambda e: errs.append('ERRO JS: '+str(e)))
        pg.on('console',lambda m: errs.append('console: '+m.text[:150]) if m.type=='error' and 'fonts' not in m.text and 'ERR_TUNNEL' not in m.text and 'Failed to load resource' not in m.text else None)
        await pg.goto(B); await pg.wait_for_timeout(800)
        await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(1500)
        if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]')
        for r in ROUTES:
          await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(650)
          k=f'{w}-{s} {r}'; rep[k]=await pg.evaluate(CHECK)
          await pg.screenshot(path=f"t4/audit/{w}-{s}-{r.replace('#/','').replace('/','_') or 'inicio'}.png",full_page=True)
        for r,sel in SHEETS:
          await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(600)
          el=pg.locator(sel).first
          if not await el.count(): rep[f'{w}-{s} folha {sel}']=['não achei o botão']; continue
          await el.click(); await pg.wait_for_timeout(700)
          rep[f'{w}-{s} folha {r} {sel}']=await pg.evaluate(CHECK)
          await pg.screenshot(path=f"t4/audit/{w}-{s}-folha-{sel.strip('[]').replace('=','-').replace('.','')}.png")
          for _ in range(3):
            x=await pg.query_selector('.overlay [data-x]')
            if not x: break
            await x.click(); await pg.wait_for_timeout(350)
        rep[f'{w}-{s} erros']=errs[:10]
        await ctx.close()
    await b.close()
  agg={}
  for k,v in rep.items():
    for i in v: agg.setdefault(i,[]).append(k)
  for i,ks in sorted(agg.items(),key=lambda x:-len(x[1])): print(f'[{len(ks)}] {i}  ← {ks[0]}')
asyncio.run(main())
