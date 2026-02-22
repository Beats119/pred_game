#!/usr/bin/env python3
"""
Test login with VISIBLE browser so you can see what's happening
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "7985531737"
PASSWORD = "rahul123"
BASE_URL = "https://bdgwina.cc"
GAME_URL = "https://bdgwina.cc/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"

async def test_visible_login():
    print("=" * 70)
    print("  TESTING LOGIN WITH VISIBLE BROWSER")
    print("  Watch the browser window to see what happens!")
    print("=" * 70)
    print()
    
    async with async_playwright() as p:
        # Launch VISIBLE browser
        browser = await p.chromium.launch(
            headless=False,  # VISIBLE!
            slow_mo=500  # Slow down actions
        )
        
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        page = await context.new_page()
        
        try:
            print("1️⃣  Going to homepage...")
            await page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30000)
            print("   Waiting for Vue.js to render (5 seconds)...")
            await asyncio.sleep(5)
            
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            # Look for login button
            print("\n2️⃣  Looking for login button/link...")
            login_selectors = [
                'button:has-text("Login")',
                'a:has-text("Login")',
                'button:has-text("Sign In")',
                '[class*="login-btn"]'
            ]
            
            login_found = False
            for selector in login_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        is_visible = await elem.is_visible()
                        if is_visible:
                            print(f"   ✅ Found login trigger: {selector}")
                            await elem.click()
                            await asyncio.sleep(3)
                            login_found = True
                            break
                except:
                    continue
            
            if not login_found:
                print("   ⚠️  No login button found, assuming form is already visible")
            
            # Wait for form
            print("\n3️⃣  Waiting for login form...")
            try:
                await page.wait_for_selector('input[type="tel"], input[type="text"]', timeout=15000)
                print("   ✅ Login form detected")
            except:
                print("   ❌ Login form not found!")
                await page.screenshot(path="logs/error_no_form.png")
                print("   Screenshot saved: logs/error_no_form.png")
                print("\n⏳ Keeping browser open for 30 seconds...")
                await asyncio.sleep(30)
                return
            
            await asyncio.sleep(2)
            
            # Fill username
            print("\n4️⃣  Filling username...")
            username_selectors = [
                'input[type="tel"]',
                'input[type="text"]',
                'input[placeholder*="phone"]',
                'input[name="username"]'
            ]
            
            username_filled = False
            for selector in username_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        is_visible = await elem.is_visible()
                        if is_visible:
                            print(f"   ✅ Filling with selector: {selector}")
                            await elem.click()
                            await asyncio.sleep(0.5)
                            await elem.fill(USERNAME)
                            username_filled = True
                            break
                except:
                    continue
            
            if not username_filled:
                print("   ❌ Could not fill username!")
                await page.screenshot(path="logs/error_username.png")
                print("\n⏳ Keeping browser open for 30 seconds...")
                await asyncio.sleep(30)
                return
            
            await asyncio.sleep(1)
            
            # Fill password
            print("\n5️⃣  Filling password...")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        is_visible = await elem.is_visible()
                        if is_visible:
                            print(f"   ✅ Filling with selector: {selector}")
                            await elem.click()
                            await asyncio.sleep(0.5)
                            await elem.fill(PASSWORD)
                            password_filled = True
                            break
                except:
                    continue
            
            if not password_filled:
                print("   ❌ Could not fill password!")
                await page.screenshot(path="logs/error_password.png")
                print("\n⏳ Keeping browser open for 30 seconds...")
                await asyncio.sleep(30)
                return
            
            await asyncio.sleep(1)
            
            # Click login button
            print("\n6️⃣  Clicking login button...")
            button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Sign In")',
                '[class*="login-btn"]'
            ]
            
            button_clicked = False
            for selector in button_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        is_visible = await elem.is_visible()
                        if is_visible:
                            print(f"   ✅ Clicking: {selector}")
                            await elem.click()
                            button_clicked = True
                            break
                except:
                    continue
            
            if not button_clicked:
                print("   ❌ Could not click login button!")
                await page.screenshot(path="logs/error_button.png")
                print("\n⏳ Keeping browser open for 30 seconds...")
                await asyncio.sleep(30)
                return
            
            # Wait for login
            print("\n7️⃣  Waiting for login to complete...")
            await asyncio.sleep(5)
            
            current_url = page.url
            print(f"   Current URL: {current_url}")
            
            if "login" in current_url.lower():
                print("   ⚠️  Still on login page - login may have failed")
                await page.screenshot(path="logs/still_on_login.png")
            else:
                print("   ✅ Navigated away from login page!")
            
            # Try to go to game
            print("\n8️⃣  Going to game page...")
            await page.goto(GAME_URL, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            
            await page.screenshot(path="logs/game_page.png", full_page=True)
            print("   Screenshot saved: logs/game_page.png")
            
            print("\n✅ Test complete!")
            print("\n⏳ Keeping browser open for 30 seconds so you can inspect...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                await page.screenshot(path="logs/error_exception.png")
                print("Screenshot saved: logs/error_exception.png")
            except:
                pass
            
            print("\n⏳ Keeping browser open for 30 seconds...")
            await asyncio.sleep(30)
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(test_visible_login())
