# Prints limpos das telas novas (claro e escuro, 390 px) para mostrar ao Caio
import asyncio, sys
from playwright.async_api import async_playwright
async def main():
  async with async_playwright() as p:
    b=await p.chromium.launch()
    for sch in ['light','dark']:
      ctx=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,color_scheme=sch); pg=await ctx.new_page()
      await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800)
      await pg.fill('#lEmail','caio@exemplo.com'); await pg.fill('#lSenha','demonstracao'); await pg.click('#lBtn'); await pg.wait_for_timeout(2500)
      if await pg.query_selector('[data-tour=skip]'): await pg.click('[data-tour=skip]'); await pg.wait_for_timeout(400)
      sh=lambda n: pg.screenshot(path=f't2/print-{n}-{sch}.png')
      # Início: próxima compra + atividade
      y=await pg.evaluate("document.querySelector('.prox').getBoundingClientRect().top+scrollY-90"); await pg.evaluate(f"scrollTo(0,{y})"); await pg.wait_for_timeout(500); await sh('1-inicio')
      await pg.evaluate("location.hash='#/atividade'"); await pg.wait_for_timeout(900); await sh('2-atividade')
      await pg.evaluate("location.hash='#/'"); await pg.wait_for_timeout(600)
      await pg.click('#tabbar [data-act=anotar]'); await pg.wait_for_timeout(700)
      await pg.fill('#aNome','Toalha de banho'); await pg.click('.overlay [data-add]'); await pg.wait_for_timeout(700); await sh('3-repetido')
      await pg.click('.overlay [data-x]'); await pg.wait_for_timeout(500)
      await pg.evaluate("location.hash='#/mercado'"); await pg.wait_for_timeout(700)
      if await pg.query_selector('.card [data-act=m-new]'): await pg.click('.card [data-act=m-new]'); await pg.wait_for_timeout(500)
      if await pg.query_selector('[data-act=m-sec][data-v="*"]'): await pg.click('[data-act=m-sec][data-v="*"]'); await pg.wait_for_timeout(400)
      await pg.evaluate("document.querySelector('.toast')?.remove()")
      y=await pg.evaluate("document.querySelector('.m-sobra').getBoundingClientRect().top+scrollY-300"); await pg.evaluate(f"scrollTo(0,{y})"); await pg.wait_for_timeout(500); await sh('4-mercado-ficou')
      await pg.click('.m-sobra [data-act=m-qty] >> nth=0'); await pg.wait_for_timeout(800); await sh('5-historico-preco')
      await ctx.close()
    await b.close()
asyncio.run(main())
