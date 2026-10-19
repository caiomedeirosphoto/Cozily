import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); ctx=await b.new_context(viewport={'width':390,'height':844}); pg=await ctx.new_page()
        await pg.goto('http://localhost:8811/index.html'); await pg.wait_for_timeout(800); await pg.click('#lBtn'); await pg.wait_for_timeout(1500)
        await pg.evaluate("location.hash='#/c/cozinha'"); await pg.wait_for_timeout(700)
        await pg.evaluate("window.scrollTo(0,600)"); await pg.wait_for_timeout(200)
        await pg.click('.item .item-main >> nth=5'); await pg.wait_for_timeout(700)
        res=await pg.evaluate("""()=>new Promise(r=>{const out=[];document.querySelector('[data-act=back]').click();const t0=performance.now();
          const f=()=>{const pg=document.querySelector('#app>.page');const it=pg&&pg.querySelector('.item');out.push([Math.round(performance.now()-t0),pg?+getComputedStyle(pg).opacity:-1,it?+getComputedStyle(it).opacity:-1,scrollY]);
            if(performance.now()-t0<450) requestAnimationFrame(f); else r(out)};requestAnimationFrame(f)})""")
        print(res[:12])
        await b.close()
asyncio.run(main())
