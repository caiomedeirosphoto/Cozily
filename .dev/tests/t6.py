import asyncio, json
from playwright.async_api import async_playwright
db = open('olddb.json').read()
fails=[]
def ok(c,m):
    print(('PASS ' if c else 'FAIL ')+m)
    if not c: fails.append(m)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); errs=[]
        ctx=await b.new_context(viewport={'width':390,'height':844}); pg=await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(300)
        await pg.evaluate("d => localStorage.setItem('cozily-preview-v6', d)", db)
        await pg.reload(); await pg.wait_for_timeout(2000)
        T=lambda: pg.inner_text('#app')
        if await pg.query_selector('.tour'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(300)
        t=await T()
        ok('Quais cômodos' not in t and 'Sua moradia' not in t, 'no onboarding for existing data')
        ok('53 de 292' in t, 'migration: 268+24 items, 53 done kept -> ' + t.split('da casa já montada')[1][:20].replace('\n',' '))
        ok('Ferramentas e utilidades' in t, 'ferramentas room present')
        ok('Chaves em dez 2028' in t, 'keys chip legacy default')
        st = json.loads(await pg.evaluate("localStorage.getItem('cozily-preview-v6')"))
        c = st['casas']['nosso-ap']
        ok(c['settings'].get('v3') is True, 'v3 flag saved')
        ok('custom-x' in c['items'], 'custom item preserved')
        ok(c['settings'].get('membros')==['caio@exemplo.com'], 'membros saved: '+str(c['settings'].get('membros')))
        await pg.reload(); await pg.wait_for_timeout(2000)
        if await pg.query_selector('.tour'): await pg.click('[data-tour=skip]')
        st2 = json.loads(await pg.evaluate("localStorage.getItem('cozily-preview-v6')"))
        ok(len(st2['casas']['nosso-ap']['items'])==292, 'no duplicate migration after reload')
        await pg.evaluate("location.hash='#/avisos'"); await pg.wait_for_timeout(600)
        ok('Garantia até ago 2027' in await T(), 'old text warranty parsed')
        await pg.evaluate("location.hash='#/i/cozinha--eletrodomesticos--air-fryer'"); await pg.wait_for_timeout(600)
        await pg.click('[data-act=edit]'); await pg.wait_for_timeout(600)
        ok(await pg.input_value('#fGar')=='2027-08-31', 'edit form converts warranty to date')
        await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
        await pg.evaluate("location.hash='#/financas'"); await pg.wait_for_timeout(600)
        tt=await T(); ok('R$ 389' in tt and 'Disponível agora\nR$ 0' in tt and 'não entra na conta' in tt, 'finance: old purchases not subtracted from empty caixinha')
        await pg.evaluate("location.hash='#/presentes'"); await pg.wait_for_timeout(600)
        ok('Monte a lista do chá' in await T(), 'presentes empty state')
        await pg.evaluate("location.hash='#/mercado'"); await pg.wait_for_timeout(600)
        ok('Montar a lista do mês' in await T(), 'mercado empty state')
        await pg.evaluate("location.hash='#/achadinhos'"); await pg.wait_for_timeout(600)
        ok('estão chegando' in await T(), 'achadinhos empty state (no offers in prod)')
        await pg.evaluate("location.hash='#/gastos'"); await pg.wait_for_timeout(600)
        ok('Caixinha da casa' in await T(), 'old #/gastos goes to Finanças')
        # small screens overflow
        for w in [320, 375, 430]:
            await pg.set_viewport_size({'width':w,'height':700})
            for h in ['#/','#/c/cozinha','#/i/banheiro--toalhas--toalhas-de-banho','#/ordem','#/financas','#/mercado','#/mercado/gastos','#/avisos','#/achadinhos','#/presentes','#/busca']:
                await pg.evaluate(f"location.hash='{h}'"); await pg.wait_for_timeout(350)
                if h=='#/mercado' and await pg.query_selector('[data-act=m-new]') and 'Montar' in await T():
                    await pg.click('[data-act=m-new]'); await pg.wait_for_timeout(400)
                over = await pg.evaluate("document.documentElement.scrollWidth - innerWidth")
                if over>0: ok(False, f'overflow {over}px at {w} {h}')
            await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(300)
            for sel in ['[data-act=settings]','.fab']:
                await pg.click(sel); await pg.wait_for_timeout(500)
                over = await pg.evaluate("Math.max(document.documentElement.scrollWidth - innerWidth, (document.querySelector('.sheet-body')||{scrollWidth:0,clientWidth:0}).scrollWidth - (document.querySelector('.sheet-body')||{clientWidth:0}).clientWidth)")
                if over>0: ok(False, f'sheet overflow {over}px at {w} {sel}')
                await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(400)
        await pg.set_viewport_size({'width':320,'height':700}); await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(500)
        await pg.screenshot(path='t2/w320-home.png')
        await pg.evaluate("location.hash='#/financas'"); await pg.wait_for_timeout(500); await pg.screenshot(path='t2/w320-fin.png')
        print('ERRS', errs); print('FAILS', fails); await b.close()
asyncio.run(main())
