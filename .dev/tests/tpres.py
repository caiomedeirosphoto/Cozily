import asyncio
from playwright.async_api import async_playwright
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for s in ['light','dark']:
      ctx=await b.new_context(viewport={'width':390,'height':844},color_scheme=s); pg=await ctx.new_page(); errs=[]
      pg.on('pageerror',lambda e: errs.append(str(e)))
      await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800); await pg.click('#lBtn'); await pg.wait_for_timeout(1500)
      await pg.evaluate("location.hash='#/presentes'"); await pg.wait_for_timeout(600)
      await pg.screenshot(path=f't2/pres-on-{s}.png')
      await pg.click('[data-act=pres-filter][data-v=add]'); await pg.wait_for_timeout(500)
      await pg.screenshot(path=f't2/pres-add-{s}.png')
      await pg.click('[data-act=pres-room][data-v=cozinha]'); await pg.wait_for_timeout(400)
      t=await pg.inner_text('#presList'); print(s,'cozinha only:', 'Toalha' not in t, len(t))
      await pg.fill('#presQ','toalha'); await pg.wait_for_timeout(300)
      t=await pg.inner_text('#presList'); print('search toalha:', t[:140].replace('\n',' | '))
      await pg.screenshot(path=f't2/pres-search-{s}.png')
      n0=await pg.evaluate("document.querySelectorAll('#presList [data-act=lista-item]').length")
      await pg.click('#presList [data-act=lista-item] >> nth=0'); await pg.wait_for_timeout(500)
      v=await pg.input_value('#presQ'); n1=await pg.evaluate("document.querySelectorAll('#presList [data-act=lista-item]').length")
      print('after toggle search kept:', v, n0, '->', n1)
      await pg.fill('#presQ','xyzabc'); await pg.wait_for_timeout(300); print('empty msg has Anotar:', 'Anotar' in await pg.inner_text('#presList'))
      print(errs); await ctx.close()
    await b.close()
asyncio.run(m())
