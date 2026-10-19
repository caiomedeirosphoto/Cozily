import asyncio
from playwright.async_api import async_playwright
res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
async def drag(pg, dx, dy, steps=8):
  bb=await pg.locator('.toast .tx').bounding_box(); x=bb['x']+bb['width']/2; y=bb['y']+bb['height']/2
  await pg.mouse.move(x,y); await pg.mouse.down()
  for k in range(1,steps+1): await pg.mouse.move(x+dx*k/steps, y+dy*k/steps); await pg.wait_for_timeout(16)
  await pg.mouse.up(); await pg.wait_for_timeout(350)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); errs=[]
    pg=await (await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2)).new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
    await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800)
    await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(2500)
    if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]')
    await pg.evaluate("location.hash='#/mercado'"); await pg.wait_for_timeout(700)
    if await pg.query_selector('.card [data-act=m-new]'): await pg.click('.card [data-act=m-new]'); await pg.wait_for_timeout(600)
    async def addtoast(n):
      await pg.fill('#mQ',n); await pg.wait_for_timeout(200); await pg.click('[data-act=m-addq]'); await pg.wait_for_timeout(400)
    await addtoast('kiwi'); ok(await pg.query_selector('.toast') is not None,'toast shown')
    await drag(pg,160,0); ok(await pg.query_selector('.toast') is None,'swipe right dismisses')
    await addtoast('manga'); await drag(pg,-160,0); ok(await pg.query_selector('.toast') is None,'swipe left dismisses')
    await addtoast('pera'); await drag(pg,0,90); ok(await pg.query_selector('.toast') is None,'swipe down dismisses (bottom toast)')
    await addtoast('uva'); await drag(pg,30,0); ok(await pg.query_selector('.toast') is not None,'short drag snaps back')
    tr=await pg.evaluate("document.querySelector('.toast').style.transform"); ok(tr in ('','none'),'snapped to place: '+tr)
    await drag(pg,0,-90); ok(await pg.query_selector('.toast') is not None,'swipe up on bottom toast does not dismiss')
    await pg.wait_for_timeout(3600); ok(await pg.query_selector('.toast') is None,'still auto-dismisses after drag')
    # undo button still works (m-rm)
    await pg.fill('#mQ',''); await pg.wait_for_timeout(200)
    await pg.click('[data-act=m-edit]'); await pg.wait_for_timeout(300)
    n0=await pg.locator('#mList .mrow').count()
    await pg.click('[data-act=m-rm] >> nth=0'); await pg.wait_for_timeout(300)
    await pg.click('.toast button'); await pg.wait_for_timeout(300)
    ok(await pg.locator('#mList .mrow').count()==n0,'Desfazer still works')
    # top toast (inside a sheet)
    await pg.click('#mList [data-act=m-qty] >> nth=0'); await pg.wait_for_timeout(600)
    await pg.evaluate("document.querySelector('.overlay').dispatchEvent(new Event('x'))")
    await pg.click('[data-act=m-edit]') if False else None
    await pg.screenshot(path='t2/swipe.png')
    print('\n'.join(res)); print('\n'.join(errs) or 'NO PAGE ERRORS'); await b.close()
asyncio.run(main())
