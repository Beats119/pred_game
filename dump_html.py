import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-blink-features=AutomationControlled'])
        context = await browser.new_context(
            viewport={"width": 414, "height": 896}, # Mobile viewport is safer for these sites
            user_agent="Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36"
        )
        page = await context.new_page()
        print("Goto login...")
        await page.goto("https://bdgwina.cc/#/login", wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(5)
        
        print("Typing credentials...")
        await page.locator('input[placeholder*="Phone"]').first.click()
        await page.keyboard.type("7985531737", delay=50)
        
        await page.locator('input[type="password"]').first.click()
        await page.keyboard.type("rahul123", delay=50)
        
        await page.locator('button:has-text("Log in")').first.click()
        
        print("Waiting for home...")
        await asyncio.sleep(8)
        
        # Kill popups
        await page.evaluate('''() => {
            const buttons = document.querySelectorAll('*');
            for (let b of buttons) {
                const text = b.innerText ? b.innerText.trim().toLowerCase() : '';
                if (text === 'confirm' || text === 'got it' || text === 'close') {
                    b.click();
                }
            }
        }''')
        await asyncio.sleep(3)
        await page.evaluate('''() => {
            const buttons = document.querySelectorAll('*');
            for (let b of buttons) {
                const text = b.innerText ? b.innerText.trim().toLowerCase() : '';
                if (text === 'confirm' || text === 'got it' || text === 'close') {
                    b.click();
                }
            }
        }''')
        
        html = await page.content()
        with open("logs/home_page_mobile.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await page.screenshot(path="logs/home_page_mobile.png", full_page=True)
        print("Saved home page HTML and screenshot.")
        await browser.close()

asyncio.run(main())
