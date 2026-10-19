import asyncio
from playwright.async_api import async_playwright
K='cozily-preview-v6'; res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); errs=[]
    for sch,w in [('light',390),('dark',320)]:
      pg=await (await b.new_context(viewport={'width':w,'height':844},device_scale_factor=2,color_scheme=sch)).new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
      await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800)
      await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(2500)
      if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]')
      await pg.evaluate("location.hash='#/mercado'"); await pg.wait_for_timeout(700)
      if await pg.query_selector('.card [data-act=m-new]'): await pg.click('.card [data-act=m-new]'); await pg.wait_for_timeout(600)
      ok(await pg.query_selector('#mQ') is not None,'search bar')
      ok('pôr o preço' in await pg.inner_text('#mTot'),'price hint when no prices')
      await pg.fill('#mQ','arroz'); await pg.wait_for_timeout(300)
      t=await pg.inner_text('#mList'); ok('Arroz' in t and 'Feijão' not in t,'search filters: '+t[:60].replace('\n',' '))
      await pg.click('#mList [data-act=m-qty] >> nth=0'); await pg.wait_for_timeout(600)
      await pg.click('.overlay #qU [data-v=kg]'); await pg.wait_for_timeout(100)
      ok('kg' in await pg.inner_text('#qPrecoL'),'label per kg')
      await pg.fill('#qPreco','6,50'); await pg.wait_for_timeout(150)
      tt=await pg.inner_text('#qTot'); ok('R$' in tt,'live total: '+tt)
      await pg.screenshot(path=f't2/merc-{sch}-qtd.png')
      await pg.click('.overlay [data-ok]'); await pg.wait_for_timeout(500)
      t=await pg.inner_text('#mList'); ok('R$' in t,'row shows price: '+t.replace('\n',' ')[:80])
      ok('Estimativa' in await pg.inner_text('#mTot'),'totals shown')
      await pg.fill('#mQ','pão de queijo'); await pg.wait_for_timeout(300)
      ok('Colocar' in await pg.inner_text('#mList'),'no result offers add')
      await pg.click('[data-act=m-addq]'); await pg.wait_for_timeout(500)
      ok(await pg.input_value('#mQ')=='' and 'Pão de queijo' in await pg.inner_text('#mList'),'added from search')
      await pg.click('#mList [data-act=m-toggle] >> nth=0'); await pg.wait_for_timeout(400)
      await pg.screenshot(path=f't2/merc-{sch}.png', full_page=False)
      v=await pg.get_attribute('[data-act=lancar]','data-v'); ok(v not in (None,''),'lancar has cart total '+str(v))
      # mark priced arroz into cart
      v=await pg.get_attribute('[data-act=lancar]','data-v'); ok(v and float(v)>0,'cart total >0: '+str(v))
      await pg.click('[data-act=lancar]'); await pg.wait_for_timeout(600)
      ok('R$' in await pg.input_value('#cVal'),'lancar prefilled '+await pg.input_value('#cVal'))
      await pg.screenshot(path=f't2/merc-{sch}-lancar.png')
    print('\n'.join(res)); print('\n'.join(errs) or 'NO PAGE ERRORS'); await b.close()
asyncio.run(main())
