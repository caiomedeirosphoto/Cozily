# Início novo (anel da Etapa 1, cômodos em fileira, atividade, atalhos), tela Cômodos e atividade nos Avisos
import asyncio
from playwright.async_api import async_playwright
res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); errs=[]
    for sch,w in [('light',390),('dark',320),('dark',390),('light',320)]:
      tag=f'{sch}-{w}'
      ctx=await b.new_context(viewport={'width':w,'height':844},device_scale_factor=2,color_scheme=sch)
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
      await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800)
      await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(2500)
      if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(300)
      await pg.wait_for_timeout(900)
      t=await pg.inner_text('#app')
      ok('Pronto pra morar' in t and 'A casa toda' in t, f'{tag} anel da etapa 1')
      p=await pg.evaluate("getComputedStyle(document.querySelector('.anel')).getPropertyValue('--p').trim()")
      ok(p not in ('','0'), f'{tag} anel preenchido ({p})')
      ok(await pg.locator('.carrossel .mini-room').count()==12, f'{tag} 11 cômodos + ver todos na fileira')
      ok(await pg.query_selector('#app .room-card') is None, f'{tag} sem quadradinhos no início')
      order=await pg.evaluate("[...document.querySelectorAll('.sec-h h2')].map(x=>x.textContent)")
      ok(order==['Cômodos','Atividade da casa','Atalhos'], f'{tag} ordem das seções {order}')
      ok('Finanças' in t and 'Mercado do mês' in t and 'Lista de presentes' in t and 'Achadinhos' in t, f'{tag} atalhos')
      w2=await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]"); ok(w2[0]<=w2[1], f'{tag} sem rolagem lateral {w2}')
      h1=await pg.evaluate("document.querySelector('.hello h1').getBoundingClientRect().height"); ok(h1<45, f'{tag} título numa linha ({h1:.0f}px)')
      await pg.screenshot(path=f't2/inicio-{tag}.png')
      await pg.click('.sec-h a[href="#/comodos"]'); await pg.wait_for_timeout(800)
      ok(await pg.locator('#app .room-card').count()==11, f'{tag} tela Cômodos com os quadradinhos')
      await pg.screenshot(path=f't2/comodos-{tag}.png')
      await pg.click('#app .room-card >> nth=0'); await pg.wait_for_timeout(700)
      ok('/c/' in pg.url, f'{tag} abre o cômodo')
      await pg.evaluate("location.hash='#/avisos'"); await pg.wait_for_timeout(800)
      ta=await pg.inner_text('#app')
      ok('ATIVIDADE DA CASA' in ta.upper() and 'Mirielly marcou como comprado' in ta, f'{tag} atividade nos avisos')
      await pg.screenshot(path=f't2/avisos-{tag}.png', full_page=True)
      await ctx.close()
    print('\n'.join(res)); print('FAILS', sum(r.startswith('FAIL') for r in res)); print('\n'.join(errs) or 'NO PAGE ERRORS'); await b.close()
asyncio.run(main())
