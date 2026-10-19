import asyncio
from playwright.async_api import async_playwright
ROUTES=['#/','#/ordem','#/mercado','#/mercado/gastos','#/financas','#/presentes','#/avisos','#/achadinhos','#/busca','#/c/cozinha','#/c/quarto','#/c/banheiro','#/i/cozinha--eletrodomesticos--geladeira','#/i/banheiro--toalhas--toalhas-de-banho','#/l/caio-e-mirielly']
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); issues=[]
        for w in [320,390]:
          for s in ['light','dark']:
            ctx=await b.new_context(viewport={'width':w,'height':780},color_scheme=s); pg=await ctx.new_page(); errs=[]
            pg.on('pageerror',lambda e: errs.append(str(e)))
            pg.on('console',lambda m: errs.append('console:'+m.text) if m.type=='error' else None)
            await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800); await pg.click('#lBtn'); await pg.wait_for_timeout(1500)
            for r in ROUTES:
                await pg.evaluate(f"location.hash='{r}'"); await pg.wait_for_timeout(450)
                t=await pg.inner_text('body')
                for bad in ['undefined','NaN','null','[object']:
                    if bad in t: issues.append((w,s,r,'texto: '+bad))
                ov=await pg.evaluate("document.documentElement.scrollWidth>innerWidth+1")
                if ov: issues.append((w,s,r,'overflow horizontal'))
                cut=await pg.evaluate("""()=>[...document.querySelectorAll('#app button, #app a, #app .item-name')].filter(e=>e.offsetWidth&&e.scrollWidth>e.clientWidth+2 && getComputedStyle(e).overflow!=='hidden' && getComputedStyle(e).textOverflow!=='ellipsis').map(e=>e.textContent.trim().slice(0,30)).slice(0,3)""")
                if cut: issues.append((w,s,r,'conteúdo vazando: '+str(cut)))
            if errs: issues.append((w,s,'erros',errs[:5]))
            await ctx.close()
        for i in issues: print(i)
        print('TOTAL', len(issues))
        await b.close()
asyncio.run(main())
