#!/usr/bin/env python3
"""
Fix the login - test with visible browser to see what's happening
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "7985531737"
PASSWORD = "rahul123"

async def test_login():
    print("Testing login with VISIBLE browser...")
    print("Watch what happens and tell me where it fails!\n")
    
    async with async_playwright() as p:
        # Launch VISIBLE browser so you can see what's happening
        browser = await p.chromium.launch(
            headless=False,  # VISIBLE!
            slow_mo=1000  # Slow down so you can see
        )
        page = await browser.new_page()
        
        try:
            print("1. Going to website...")
            await page.goto("https://bdgwina.cc", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(3)
            
            print("2. Looking for login form...")
            
            # Take screenshot
            await page.screenshot(path="logs/step1_homepage.png")
            print("   Screenshot: logs/step1_homepage.png")
            
            # Try to find phone input
            phone_input = await page.query_selector('input[type="tel"]')
            if not phone_input:
                phone_input = await page.query_selector('input[type="text"]')
            
            if phone_input:
                print("3. Found phone input, filling...")
                await phone_input.click()
                await phone_input.fill(USERNAME)
                await asyncio.sleep(2)
                
                await page.screenshot(path="logs/step2_phone_filled.png")
                print("   Screenshot: logs/step2_phone_filled.png")
            else:
                print("   ❌ Could not find phone input!")
                await page.screenshot(path="logs/error_no_phone_input.png")
                return
            
            # Find password
            password_input = await page.query_selector('input[type="password"]')
            if password_input:
                print("4. Found password input, filling...")
                await password_input.click()
                await password_input.fill(PASSWORD)
                await asyncio.sleep(2)
                
                await page.screenshot(path="logs/step3_password_filled.png")
                print("   Screenshot: logs/step3_password_filled.png")
            else:
                print("   ❌ Could not find password input!")
                await page.screenshot(path="logs/error_no_password_input.png")
                return
            
            # Find login button
            print("5. Looking for login button...")
            login_button = await page.query_selector('button[type="submit"]')
            if not login_button:
                # Try other selectors
                login_button = await page.query_selector('button:has-text("Login")')
            if not login_button:
                login_button = await page.query_selector('[class*="login-btn"]')
            
            if login_button:
                print("6. Clicking login button...")
                await login_button.click()
                await asyncio.sleep(5)
                
                await page.screenshot(path="logs/step4_after_login.png")
                print("   Screenshot: logs/step4_after_login.png")
                
                # Check if we're logged in
                current_url = page.url
                print(f"\n   Current URL: {current_url}")
                
                if "login" not in current_url.lower():
                    print("\n✅ LOGIN SUCCESSFUL!")
                    
                    # Try to go to game
                    print("\n7. Going to game page...")
                    await page.goto("https://bdgwina.cc/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo", wait_until="networkidle")
                    await asyncio.sleep(5)
                    
                    await page.screenshot(path="logs/step5_game_page.png", full_page=True)
                    print("   Screenshot: logs/step5_game_page.png")
                    
                    print("\n✅ Check the screenshots to see if we're on the game page!")
                else:
                    print("\n❌ Still on login page - login failed")
            else:
                print("   ❌ Could not find login button!")
                await page.screenshot(path="logs/error_no_login_button.png")
            
            print("\n⏳ Keeping browser open for 30 seconds so you can inspect...")
            await asyncio.sleep(30)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await page.screenshot(path="logs/error_exception.png")
        
        finally:
            await browser.close()
            print("\n✅ Done! Check the screenshots in logs/ folder")

if __name__ == "__main__":
    print("=" * 70)
    print("  TESTING LOGIN WITH VISIBLE BROWSER")
    print("=" * 70)
    print()
    asyncio.run(test_login())
