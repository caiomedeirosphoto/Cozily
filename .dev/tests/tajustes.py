import asyncio, re, urllib.parse, json
from playwright.async_api import async_playwright
B='http://localhost:8811/index.html'; K='cozily-preview-v6'
res=[]
def ok(c,m): res.append(('PASS ' if c else 'FAIL ')+m)
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch(); errs=[]
    for sch in ['light','dark']:
      ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,color_scheme=sch)
      pg=await ctx.new_page(); pg.on('pageerror',lambda e: errs.append(str(e)))
      db=lambda: pg.evaluate(f"JSON.parse(localStorage.getItem('{K}'))")
      async def logout(): await pg.evaluate(f"(()=>{{const d=JSON.parse(localStorage.getItem('{K}'));delete d.session;localStorage.setItem('{K}',JSON.stringify(d))}})()"); await pg.goto(B); await pg.wait_for_timeout(900)
      async def login(e,s='demonstracao'):
        if await pg.query_selector('[data-act=authmode][data-v=entrar]'): await pg.click('[data-act=authmode][data-v=entrar]'); await pg.wait_for_timeout(150)
        await pg.fill('#lEmail',e); await pg.fill('#lSenha',s); await pg.click('#lBtn'); await pg.wait_for_timeout(1500)
        if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(200)
      async def ajustes():
        await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(1200)
        if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(300)
        await pg.click('[data-act=settings]'); await pg.wait_for_timeout(600)
      async def closesheet(): await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(450)
      await pg.goto(B); await pg.wait_for_timeout(900); await login('caio@exemplo.com')
      await ajustes(); t=await pg.inner_text('.overlay')
      ok(all(x in t for x in ['A CASA','NO CELULAR','SUA CONTA','Privacidade','Excluir conta','Erros do app']) or all(x.lower() in t.lower() for x in ['a casa','no celular','sua conta','privacidade','excluir conta','erros do app']),'settings sections')
      await pg.screenshot(path=f't2/aj-{sch}-1.png',full_page=True)
      sh=await pg.query_selector('.overlay .sheet') or await pg.query_selector('.overlay')
      await pg.evaluate("document.querySelector('.overlay .sheet-body, .overlay .sheet')?.scrollTo(0,99999)"); await pg.wait_for_timeout(200)
      await pg.screenshot(path=f't2/aj-{sch}-2.png')
      await pg.click('[data-go=privacidade]'); await pg.wait_for_timeout(700)
      t=await pg.inner_text('.overlay'); ok('LGPD' in t and 'Excluir conta' in t,'privacy sheet'); await pg.screenshot(path=f't2/aj-{sch}-priv.png'); await closesheet()
      # name
      await ajustes(); await pg.click('[data-go=nome]'); await pg.wait_for_timeout(700); await pg.fill('#nmIn','Caio D'); await pg.click('.overlay [data-s]'); await pg.wait_for_timeout(500)
      d=await db(); ok(d['users']['caio@exemplo.com']['nome']=='Caio D','name saved')
      # error log
      await pg.evaluate("setTimeout(()=>{throw new Error('erro-de-teste-123')},0)"); await pg.wait_for_timeout(400)
      d=await db(); ok(any('erro-de-teste-123' in e['msg'] for e in d.get('erros',[])),'error logged')
      await ajustes(); await pg.click('[data-go=erros]'); await pg.wait_for_timeout(900)
      ok('erro-de-teste-123' in await pg.inner_text('.overlay'),'errors viewer'); await pg.screenshot(path=f't2/aj-{sch}-erros.png'); await closesheet()
      # invite Ana and have her join
      await ajustes(); await pg.click('[data-go=juntos]'); await pg.wait_for_timeout(700)
      if await pg.query_selector('#jOutro'): await pg.click('#jOutro'); await pg.wait_for_timeout(200)
      await pg.fill('#jQuem','Ana'); await pg.fill('#jRel','Amiga'); await pg.click('#jCriar'); await pg.wait_for_timeout(700); href=await pg.get_attribute('#jWa','href')
      async with ctx.expect_page() as pi: await pg.click('#jWa')
      await (await pi.value).close(); await pg.wait_for_timeout(500)
      code=re.search(r'\?c=([\w-]+)',urllib.parse.unquote(href)).group(1)
      await logout(); await pg.goto(B+'?c='+code); await pg.wait_for_timeout(1200)
      await pg.fill('#lEmail',f'ana-{sch}@t.com'); await pg.fill('#lSenha','123456'); await pg.fill('#lSenha2','123456'); await pg.click('#lBtn'); await pg.wait_for_timeout(1800)
      ok('Você entrou no' in await pg.inner_text('#app'),'ana joined')
      d=await db(); ok('Ana' in d['casas']['nosso-ap']['settings'].get('nomes',''),'Ana entrou na saudação')
      # caio removes ana
      await logout(); await login('caio@exemplo.com'); await ajustes(); await pg.click('[data-go=juntos]'); await pg.wait_for_timeout(700)
      await pg.click(f'[data-rm="ana-{sch}@t.com"]'); await pg.wait_for_timeout(300)
      await pg.screenshot(path=f't2/aj-{sch}-tirar.png')
      await pg.click(f'[data-rmsim="ana-{sch}@t.com"]'); await pg.wait_for_timeout(500)
      d=await db(); st=d['casas']['nosso-ap']['settings']
      ok(f'ana-{sch}@t.com' not in st['membros'] and f'ana-{sch}@t.com' not in d['convites'],'ana removed')
      ok(st.get('nomes')=='Caio e Mirielly','saudação sem a Ana: '+str(st.get('nomes')))
      ok(not await pg.query_selector('[data-rm="mirielly@exemplo.com"]'),'pending invite has no Tirar (uses Cancelar)')
      ok(not await pg.query_selector('[data-rm="caio@exemplo.com"]'),'cannot remove self')
      await closesheet()
      # ana logs in -> own casa (onboarding)
      await logout(); await login(f'ana-{sch}@t.com','123456')
      ok(await pg.query_selector('#obCasa') is not None,'removed ana lands in own new casa')
      # ana finishes onboarding quickly, then deletes account as sole owner
      await pg.fill('#obCasa','Cantinho Ana'); await pg.click('[data-act=ob-next]'); await pg.wait_for_timeout(700)
      await pg.click('[data-act=ob-next]'); await pg.wait_for_timeout(600); await pg.click('[data-act=ob-next]'); await pg.wait_for_timeout(600)
      if await pg.query_selector('[data-act=ob-finish]'): await pg.click('[data-act=ob-finish]'); await pg.wait_for_timeout(1000)
      while await pg.query_selector('.link-btn[data-act=post-next]') or await pg.query_selector('[data-act=post-next]'):
        el=await pg.query_selector('.link-btn[data-act=post-next]') or await pg.query_selector('[data-act=post-next]'); await el.click(); await pg.wait_for_timeout(700)
      if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]')
      d=await db(); uid=d['users'][f'ana-{sch}@t.com']['uid']; ok(uid in d['casas'] and len(d['casas'][uid]['items'])>0,'ana own casa exists')
      await ajustes(); await pg.click('[data-go=excluir]'); await pg.wait_for_timeout(700)
      t=await pg.inner_text('.overlay'); ok('apaga tudo' in t,'sole owner warned all data goes'); await pg.screenshot(path=f't2/aj-{sch}-excluir.png')
      await pg.fill('#exSenha','errada'); await pg.fill('#exOk','excluir'); await pg.click('.overlay [data-s]'); await pg.wait_for_timeout(500)
      ok('Senha errada' in await pg.inner_text('#exErr'),'wrong password msg')
      await pg.fill('#exSenha','123456'); await pg.fill('#exOk','nao'); await pg.click('.overlay [data-s]'); await pg.wait_for_timeout(300)
      ok('EXCLUIR' in await pg.inner_text('#exErr'),'needs EXCLUIR')
      await pg.fill('#exOk','EXCLUIR'); await pg.click('.overlay [data-s]'); await pg.wait_for_timeout(1500)
      d=await db(); ok(f'ana-{sch}@t.com' not in d['users'] and uid not in d['casas'],'sole owner: account+casa deleted')
      ok(await pg.query_selector('#lBtn') is not None,'back at login')
      # member (mirielly) deletes account -> casa stays
      await login('mirielly@exemplo.com')
      while await pg.query_selector('[data-act=post-next]'):
        el=await pg.query_selector('.link-btn[data-act=post-next]') or await pg.query_selector('[data-act=post-next]'); await el.click(); await pg.wait_for_timeout(700)
      if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]')
      await ajustes(); await pg.click('[data-go=excluir]'); await pg.wait_for_timeout(700)
      t=await pg.inner_text('.overlay'); ok('continua com' in t,'member warned list stays: '+t[:160].replace('\n',' '))
      await pg.fill('#exSenha','demonstracao'); await pg.fill('#exOk','EXCLUIR'); await pg.click('.overlay [data-s]'); await pg.wait_for_timeout(1500)
      d=await db(); ok('mirielly@exemplo.com' not in d['users'] and 'nosso-ap' in d['casas'] and 'mirielly@exemplo.com' not in d['casas']['nosso-ap']['settings'].get('membros',[]) and len(d['casas']['nosso-ap']['items'])>100,'member deleted, casa intact')
      await ctx.close()
    print('\n'.join(res)); print('\n'.join(errs) or 'NO PAGE ERRORS'); await b.close()
asyncio.run(main())
