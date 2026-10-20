# As 4 ideias de 19/10: mercado (ficou do mês passado + histórico de preço), item repetido, próxima compra e atividade da casa
import asyncio
from playwright.async_api import async_playwright
res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
async def login(pg, email='caio@exemplo.com'):
  await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800)
  await pg.fill('#lEmail',email); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(2500)
  if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(300)
async def overflow(pg, nome):
  w=await pg.evaluate("[document.documentElement.scrollWidth, innerWidth]")
  ok(w[0]<=w[1], f'{nome}: sem rolagem lateral {w}')
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); errs=[]
    for sch,w in [('light',390),('dark',320),('dark',390),('light',320)]:
      tag=f'{sch}-{w}'
      ctx=await b.new_context(viewport={'width':w,'height':844},device_scale_factor=2,color_scheme=sch)
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
      await login(pg)
      # ---------- 3. Próxima compra
      t=await pg.inner_text('#app')
      ok('Próxima compra' in t.title() or 'PRÓXIMA COMPRA' in t, f'{tag} card próxima compra')
      prox=await pg.inner_text('.prox')
      ok(('Etapa 1' in prox or (w<=320 and 'Oferta' in prox)) and 'previsto' in prox, f'{tag} próxima: etapa 1 com valor ({prox[:70]!r})')
      ok('Dá pra comprar' in prox or 'Faltam' in prox, f'{tag} próxima compara com a caixinha')
      await overflow(pg, tag+' início')
      await pg.locator('.prox').scroll_into_view_if_needed(); await pg.wait_for_timeout(300)
      await pg.locator('.prox').screenshot(path=f't2/novo-proxima-{tag}.png')
      # ---------- 4. Atividade (home + tela)
      ok('Atividade da casa' in t, f'{tag} atividade no início')
      ok('Mirielly marcou como comprado: Toalhas de banho' in t, f'{tag} feed mostra Mirielly')
      ok('Tia Ana reservou' in t or 'Padrinhos reservou' in t or 'Mirielly' in t, f'{tag} feed tem reservas/pessoas')
      await pg.evaluate("location.hash='#/atividade'"); await pg.wait_for_timeout(700)
      ta=await pg.inner_text('#app')
      ok('HOJE' in ta.upper() and 'ONTEM' in ta.upper(), f'{tag} atividade agrupada por dia')
      ok('Caio anotou' not in ta and 'Você anotou Cortina blecaute' in ta, f'{tag} "Você" para as próprias ações')
      ok('reservou' in ta, f'{tag} reservas de convidados no feed')
      await overflow(pg, tag+' atividade')
      await pg.screenshot(path=f't2/novo-atividade-{tag}.png')
      # ---------- 2. Item repetido
      await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(600)
      await pg.click('#tabbar [data-act=anotar]'); await pg.wait_for_timeout(700)
      await pg.fill('#aNome','toalha de banho'); await pg.click('.overlay [data-add]'); await pg.wait_for_timeout(500)
      rep=await pg.inner_text('#aRep') if await pg.is_visible('#aRep') else ''
      ok('Já tem' in rep and 'Toalhas de banho' in rep and 'no Banheiro' in rep, f'{tag} aviso repetido: {rep[:80]!r}')
      await pg.screenshot(path=f't2/novo-repetido-{tag}.png')
      n0=await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('cozily-preview-v6')).casas['nosso-ap'].items).length")
      await pg.click('[data-rep-ok]'); await pg.wait_for_timeout(600)
      n1=await pg.evaluate("Object.keys(JSON.parse(localStorage.getItem('cozily-preview-v6')).casas['nosso-ap'].items).length")
      ok(n1==n0+1, f'{tag} "anotar mesmo assim" anota ({n0}->{n1})')
      ok(not await pg.is_visible('#aRep'), f'{tag} aviso some depois de anotar')
      # nome novo não avisa
      await pg.fill('#aNome','Abajur de leitura xyz'); await pg.click('.overlay [data-add]'); await pg.wait_for_timeout(500)
      ok(not await pg.is_visible('#aRep'), f'{tag} nome novo não avisa')
      # abrir o existente
      await pg.fill('#aNome','Geladeira'); await pg.click('.overlay [data-add]'); await pg.wait_for_timeout(500)
      ok(await pg.is_visible('#aRep') and 'na Cozinha' in await pg.inner_text('#aRep'), f'{tag} aviso "na Cozinha"')
      await pg.click('[data-rep-open]'); await pg.wait_for_timeout(900)
      ok('/i/cozinha--eletrodomesticos--geladeira' in pg.url and not await pg.query_selector('.overlay'), f'{tag} abrir o existente vai pro item')
      # atividade registrou as anotações
      await pg.evaluate("location.hash='#/atividade'"); await pg.wait_for_timeout(600)
      ta=await pg.inner_text('#app')
      ok('Você anotou toalha de banho' in ta and 'Você anotou Abajur de leitura xyz' in ta, f'{tag} anotar grava atividade')
      # marcar comprado grava atividade
      await pg.evaluate("location.hash='#/i/cozinha--eletrodomesticos--cooktop'"); await pg.wait_for_timeout(700)
      await pg.click('main [data-act=toggle]'); await pg.wait_for_timeout(700)
      await pg.fill('#pPago','430'); await pg.click('.overlay [data-confirm]'); await pg.wait_for_timeout(700)
      await pg.evaluate("location.hash='#/atividade'"); await pg.wait_for_timeout(600)
      ta=await pg.inner_text('#app')
      ok('Você marcou como comprado: Cooktop' in ta and 'R$ 430' in ta, f'{tag} marcar comprado grava atividade')
      # ---------- 1. Mercado
      await pg.evaluate("location.hash='#/mercado'"); await pg.wait_for_timeout(700)
      if await pg.query_selector('.card [data-act=m-new]'): await pg.click('.card [data-act=m-new]'); await pg.wait_for_timeout(700)
      tm=await pg.inner_text('#mList')
      ok(tm.upper().startswith('FICOU DO MÊS PASSADO'), f'{tag} seção "Ficou do mês passado" no topo: {tm[:40]!r}')
      sob=await pg.inner_text('.m-sobra')
      ok(all(x in sob for x in ['Azeite','Queijo','Amaciante','Limão']) and 'Arroz' not in sob, f'{tag} só o que não foi comprado')
      ok(await pg.locator('#mList .mrow').count() > 40, f'{tag} lista completa continua')
      await overflow(pg, tag+' mercado')
      await pg.locator('.m-sobra').scroll_into_view_if_needed()
      await pg.screenshot(path=f't2/novo-mercado-sobrou-{tag}.png')
      # marcar um do "ficou" continua na seção, riscado
      await pg.click('.m-sobra [data-act=m-toggle] >> nth=0'); await pg.wait_for_timeout(400)
      ok('1 de 4' in await pg.inner_text('.m-sobra .grp-h'), f'{tag} contador da seção')
      # histórico de preço
      await pg.fill('#mQ','azeite'); await pg.wait_for_timeout(300)
      await pg.click('#mList [data-act=m-qty] >> nth=0'); await pg.wait_for_timeout(700)
      h=await pg.inner_text('#qHist')
      mes3=await pg.evaluate("(()=>{const d=new Date();d.setMonth(d.getMonth()-3);return ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][d.getMonth()]})()")
      ok(f'Subiu 15% desde {mes3}' in h, f'{tag} histórico "subiu": {h[:60]!r}')
      await pg.screenshot(path=f't2/novo-preco-{tag}.png')
      await pg.fill('#qPreco','35'); await pg.wait_for_timeout(200)
      ok('Caiu 10%' in await pg.inner_text('#qVar'), f'{tag} histórico muda com o preço digitado: {await pg.inner_text("#qVar")!r}')
      await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
      await pg.fill('#mQ','banana'); await pg.wait_for_timeout(300)
      await pg.click('#mList [data-act=m-qty] >> nth=0'); await pg.wait_for_timeout(700)
      ok('Caiu' in await pg.inner_text('#qVar'), f'{tag} banana caiu')
      await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
      await pg.fill('#mQ','sal'); await pg.wait_for_timeout(300)
      await pg.click('#mList [data-act=m-qty] >> nth=0'); await pg.wait_for_timeout(700)
      ok(await pg.query_selector('#qHist') is None, f'{tag} sem histórico quando não tem preço')
      await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
      await pg.fill('#mQ',''); await pg.dispatch_event('#mQ','input'); await pg.wait_for_timeout(200)
      # lançar compra grava atividade
      await pg.click('[data-act=lancar]'); await pg.wait_for_timeout(600)
      await pg.fill('#cVal','R$ 210'); await pg.click('.overlay [data-go]'); await pg.wait_for_timeout(700)
      await pg.evaluate("location.hash='#/atividade'"); await pg.wait_for_timeout(600)
      ta=await pg.inner_text('#app')
      ok('Você lançou uma compra do mercado' in ta and 'R$ 210' in ta, f'{tag} lançar compra grava atividade')
      # mês seguinte: só o que ficou sem comprar
      await pg.evaluate("location.hash='#/mercado'"); await pg.wait_for_timeout(600)
      await pg.click('.btns2 [data-act=m-new]'); await pg.wait_for_timeout(700)
      sob=await pg.inner_text('.m-sobra') if await pg.query_selector('.m-sobra') else ''
      ok('Azeite' not in sob and 'Queijo' in sob and len([1 for x in sob.split('\n') if x.strip()])>3, f'{tag} virada do mês seguinte: {sob[:60]!r}')
      # Mirielly vê o que o Caio fez
      await pg.evaluate("document.querySelector('.overlay')?.remove()")
      await pg.evaluate("localStorage.setItem('cozily-preview-v6', JSON.stringify(Object.assign(JSON.parse(localStorage.getItem('cozily-preview-v6')), {session: undefined})))")
      await login(pg,'mirielly@exemplo.com')
      if await pg.query_selector('[data-act=post-next]'):
        for _ in range(4):
          if await pg.query_selector('[data-act=post-next]'): await pg.click('[data-act=post-next]'); await pg.wait_for_timeout(400)
      await pg.evaluate("location.hash='#/atividade'"); await pg.wait_for_timeout(700)
      ta=await pg.inner_text('#app')
      ok('Caio marcou como comprado: Cooktop' in ta and 'Você marcou como comprado: Toalhas de banho' in ta, f'{tag} Mirielly vê "Caio ..." e "Você ..."')
      await ctx.close()
    print('\n'.join(res)); print('FAILS', sum(r.startswith('FAIL') for r in res)); print('\n'.join(errs) or 'NO PAGE ERRORS'); await b.close()
asyncio.run(main())
