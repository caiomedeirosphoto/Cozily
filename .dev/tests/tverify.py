import asyncio
from playwright.async_api import async_playwright
async def m():
  async with async_playwright() as p:
    b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':390,'height':844}); errs=[]
    pg.on('pageerror',lambda e: errs.append(str(e)))
    await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800)
    await pg.click('[data-act=authmode][data-v=criar]'); await pg.wait_for_timeout(200)
    await pg.fill('#lNome','Bia'); await pg.fill('#lEmail','bia+verificar@teste.com'); await pg.fill('#lSenha','123456'); (await pg.query_selector('#lSenha2')) and await pg.fill('#lSenha2','123456'); await pg.click('#lBtn'); await pg.wait_for_timeout(1200)
    t=await pg.inner_text('#app'); print('verify screen:', 'Confirma seu e-mail' in t)
    await pg.screenshot(path='t2/verify.png')
    await pg.click('[data-act=verify-ok]'); await pg.wait_for_timeout(600)
    print('still blocked before confirming:', 'Confirma seu e-mail' in await pg.inner_text('#app'))
    await pg.click('[data-act=verify-send]'); await pg.wait_for_timeout(400)
    await pg.click('[data-act=verify-ok]'); await pg.wait_for_timeout(1500)
    t=await pg.inner_text('#app'); print('after confirm goes to onboarding:', 'Confirma seu e-mail' not in t, t[:60].replace('\n',' | '))
    print(errs); await b.close()
asyncio.run(m())
