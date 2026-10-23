import asyncio
from playwright.async_api import async_playwright
B='http://localhost:8811/index.html'; K='cozily-preview-v6'; res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); errs=[]
    for w,sch in [(390,'light'),(320,'dark')]:
      ctx=await b.new_context(viewport={'width':w,'height':780},device_scale_factor=2,color_scheme=sch)
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
      db=lambda: pg.evaluate(f"JSON.parse(localStorage.getItem('{K}'))")
      async def tour():
        if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(300)
      async def home(): await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(700); await tour()
      # Caio (nosso-ap) não vê nada de teste
      await pg.goto(B); await pg.wait_for_timeout(800)
      await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(1500); await tour()
      ok(not await pg.query_selector('.plano-bar') and not await pg.query_selector('.plano-fim'),'casa do Caio sem teste')
      await pg.evaluate(f"(()=>{{const d=JSON.parse(localStorage.getItem('{K}'));delete d.session;localStorage.setItem('{K}',JSON.stringify(d))}})()")
      # conta nova
      await pg.goto(B); await pg.wait_for_timeout(900)
      await pg.click('[data-act=authmode][data-v=criar]'); await pg.wait_for_timeout(200)
      await pg.fill('#lNome','Bia'); await pg.fill('#lEmail',f'bia-{w}@t.com'); await pg.fill('#lSenha','123456'); (await pg.query_selector('#lSenha2')) and await pg.fill('#lSenha2','123456')
      await pg.click('#lBtn'); await pg.wait_for_timeout(1300)
      await pg.fill('#obCasa','Casa da Bia'); await pg.click('[data-act=ob-next]'); await pg.wait_for_timeout(700)
      await pg.click('[data-act=ob-next]'); await pg.wait_for_timeout(600); await pg.click('[data-act=ob-next]'); await pg.wait_for_timeout(600)
      if await pg.query_selector('[data-act=ob-finish]'): await pg.click('[data-act=ob-finish]'); await pg.wait_for_timeout(1000)
      while await pg.query_selector('[data-act=post-next]'):
        await (await pg.query_selector('.link-btn[data-act=post-next]') or await pg.query_selector('[data-act=post-next]')).click(); await pg.wait_for_timeout(600)
      await home()
      d=await db(); uid=d['users'][f'bia-{w}@t.com']['uid']
      ok(uid in (d.get('testes') or {}),'teste começou ao criar a conta')
      t=await pg.inner_text('.plano-bar') if await pg.query_selector('.plano-bar') else ''
      ok('faltam 7 dias' in t,'barra do teste: '+t.replace('\n',' '))
      sw=await pg.evaluate('document.documentElement.scrollWidth'); ok(sw<=w,f'sem rolagem lateral {sw}')
      await pg.screenshot(path=f't2/teste-{w}-{sch}-1.png')
      # durante o teste dá pra anotar
      await pg.click('.fab'); await pg.wait_for_timeout(600)
      ok('Liberar o Cozily' not in await pg.inner_text('body'),'no teste o + abre o anotar'); await pg.keyboard.press('Escape'); await pg.wait_for_timeout(400)
      if await pg.query_selector('.overlay [data-x]'): await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
      # abrir a tela de liberar
      await pg.click('.plano-bar'); await pg.wait_for_timeout(600)
      t=await pg.inner_text('.overlay'); ok('R$ 39,90' in t and 'R$ 49,90' in t and '-20%' in t and f'bia-{w}@t.com' in t,'tela de liberar com preço e e-mail')
      await pg.screenshot(path=f't2/teste-{w}-{sch}-2.png')
      await pg.click('[data-demo=acabar]'); await pg.wait_for_timeout(900); await home()
      ok(await pg.query_selector('.plano-fim') is not None,'aviso de teste acabou')
      await pg.screenshot(path=f't2/teste-{w}-{sch}-3.png', full_page=True)
      # bloqueado: + e marcar abrem a tela de liberar, e nada muda
      n0=len((await db())['casas'][uid]['items'])
      await pg.click('.fab'); await pg.wait_for_timeout(600)
      ok('Liberar o Cozily' in await pg.inner_text('body'),'+ abre liberar'); await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
      ok(len((await db())['casas'][uid]['items'])==n0,'nada foi criado')
      await pg.evaluate("location.hash='#/comodos'"); await pg.wait_for_timeout(600)
      await pg.locator('.room-card, a.mini-room').first.click(); await pg.wait_for_timeout(700)
      chk=pg.locator('[data-act=toggle]').first
      if await chk.count():
        await chk.click(); await pg.wait_for_timeout(600)
        ok('Liberar o Cozily' in await pg.inner_text('body'),'marcar abre liberar'); await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
      else: ok(False,'sem item pra marcar')
      # ver continua livre
      await pg.evaluate("location.hash='#/financas'"); await pg.wait_for_timeout(500)
      ok('Liberar o Cozily' not in await pg.inner_text('body'),'navegar continua livre')
      # pagar libera
      await home(); await pg.click('.plano-fim [data-act=plano]'); await pg.wait_for_timeout(600)
      await pg.click('[data-demo=pagar]'); await pg.wait_for_timeout(1000); await home()
      ok(not await pg.query_selector('.plano-fim') and not await pg.query_selector('.plano-bar'),'pago: sem aviso')
      await pg.click('.fab'); await pg.wait_for_timeout(600)
      ok('Liberar o Cozily' not in await pg.inner_text('body'),'pago: + abre anotar')
      await ctx.close()
    ok(not errs,'sem erros '+str(errs[:2]))
    await b.close()
  for r in res: print(r)
  print('FAILS',[r for r in res if r.startswith('FAIL')])
asyncio.run(main())
