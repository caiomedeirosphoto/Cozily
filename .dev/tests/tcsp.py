import asyncio
from playwright.async_api import async_playwright
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':844}); msgs=[]
    pg.on('console',lambda m: msgs.append(m.text) if ('Content Security' in m.text or 'CSP' in m.text or 'Refused' in m.text) else None)
    pg.on('pageerror',lambda e: msgs.append('ERR '+str(e)))
    await pg.goto('http://localhost:8811/csp.html'); await pg.wait_for_timeout(1200)
    await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); (await pg.query_selector('#lSenha2')) and await pg.fill('#lSenha2','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(1500)
    print('logged in, app shows:', (await pg.inner_text('#app'))[:60].replace('\n',' | '))
    await pg.evaluate("location.hash='#/i/cozinha--eletrodomesticos--geladeira'"); await pg.wait_for_timeout(500)
    print('CSP msgs:', msgs[:8]); await b.close()
asyncio.run(m())
