#!/usr/bin/env python3
"""
Fetch current live Big/Small pattern from BDG WIN WinGo 30S
"""
import asyncio
from playwright.async_api import async_playwright

USERNAME = "7985531737"
PASSWORD = "rahul123"
GAME_URL = "https://bdgwina.cc/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"

async def fetch_current():
    async with async_playwright() as p:
        print("🌐 Connecting to BDG WIN...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Login
            print("🔐 Logging in...")
            await page.goto("https://bdgwina.cc", wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # Fill login
            username_input = await page.query_selector('input[type="text"], input[type="tel"]')
            password_input = await page.query_selector('input[type="password"]')
            
            if username_input and password_input:
                await username_input.fill(USERNAME)
                await password_input.fill(PASSWORD)
                
                login_btn = await page.query_selector('button[type="submit"]')
                if login_btn:
                    await login_btn.click()
                    await asyncio.sleep(4)
            
            # Go to game
            print("🎮 Opening WinGo 30S...")
            await page.goto(GAME_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)
            
            # Take screenshot
            await page.screenshot(path="logs/live_game.png", full_page=True)
            print("📸 Screenshot saved: logs/live_game.png")
            
            # Extract Big/Small data
            print("\n📊 Extracting Big/Small pattern...")
            
            data = await page.evaluate("""
                () => {
                    const results = [];
                    
                    // Look for rows with Big/Small text
                    const rows = document.querySelectorAll('tr, [class*="row"], [class*="item"], [class*="record"], [class*="history"]');
                    
                    console.log(`Found ${rows.length} rows`);
                    
                    rows.forEach((row, idx) => {
                        if (idx >= 30) return; // Get last 30
                        
                        const text = row.innerText || row.textContent || '';
                        
                        // Look for Big or Small
                        const hasBig = /\\b(Big|BIG|big)\\b/.test(text);
                        const hasSmall = /\\b(Small|SMALL|small)\\b/.test(text);
                        
                        if (hasBig || hasSmall) {
                            // Extract period
                            const periodMatch = text.match(/\\d{10,}/);
                            const period = periodMatch ? periodMatch[0] : '';
                            
                            // Extract number
                            const numberMatch = text.match(/\\b([0-9])\\b/);
                            const number = numberMatch ? parseInt(numberMatch[1]) : null;
                            
                            if (number !== null) {
                                results.push({
                                    period: period,
                                    number: number,
                                    bigSmall: hasBig ? 'Big' : 'Small'
                                });
                            }
                        }
                    });
                    
                    return results;
                }
            """)
            
            if data and len(data) > 0:
                print(f"\n✅ Found {len(data)} results!\n")
                print("=" * 70)
                print(f"{'#':<4} {'Period':<15} {'Number':<8} {'Big/Small':<10}")
                print("=" * 70)
                
                # Show results (newest first)
                for i, r in enumerate(data[:20]):
                    print(f"{i+1:<4} {r['period']:<15} {r['number']:<8} {r['bigSmall']:<10}")
                
                print("=" * 70)
                
                # Build Big/Small sequence
                sequence = [r['bigSmall'][0] for r in data]  # B or S
                sequence_str = "-".join(sequence[:20])
                
                print(f"\n🎯 CURRENT BIG/SMALL PATTERN:")
                print(f"   Last 20: {sequence_str}")
                print(f"   Last 10: {'-'.join(sequence[:10])}")
                print(f"   Last 5:  {'-'.join(sequence[:5])}")
                
                # Check for patterns
                print(f"\n🔍 Pattern Analysis:")
                patterns_found = []
                
                # Alternating 5
                if sequence[:5] == ['B', 'S', 'B', 'S', 'B']:
                    patterns_found.append("✅ Alternating 5 (B-S-B-S-B)")
                elif sequence[:5] == ['S', 'B', 'S', 'B', 'S']:
                    patterns_found.append("✅ Alternating 5 (S-B-S-B-S)")
                
                # Triple B
                if sequence[:3] == ['B', 'B', 'B']:
                    patterns_found.append("✅ Triple B (B-B-B)")
                
                # Triple S
                if sequence[:3] == ['S', 'S', 'S']:
                    patterns_found.append("✅ Triple S (S-S-S)")
                
                # Long Run B
                if len(sequence) >= 4 and all(s == 'B' for s in sequence[:4]):
                    length = 4
                    while length < len(sequence) and sequence[length] == 'B':
                        length += 1
                    patterns_found.append(f"✅ Long Run B ({length} consecutive)")
                
                # Long Run S
                if len(sequence) >= 4 and all(s == 'S' for s in sequence[:4]):
                    length = 4
                    while length < len(sequence) and sequence[length] == 'S':
                        length += 1
                    patterns_found.append(f"✅ Long Run S ({length} consecutive)")
                
                if patterns_found:
                    for p in patterns_found:
                        print(f"   {p}")
                else:
                    print("   ⚪ No patterns detected in current sequence")
                    
            else:
                print("\n❌ Could not extract Big/Small data")
                print("The page structure may be different than expected.")
            
            # Save HTML
            html = await page.content()
            with open("logs/live_game.html", "w", encoding="utf-8") as f:
                f.write(html)
            print("\n💾 HTML saved: logs/live_game.html")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                await page.screenshot(path="logs/error.png")
                print("📸 Error screenshot: logs/error.png")
            except:
                pass
        
        finally:
            await browser.close()

if __name__ == "__main__":
    print("=" * 70)
    print("  FETCHING LIVE BIG/SMALL PATTERN FROM BDG WIN")
    print("=" * 70)
    print()
    asyncio.run(fetch_current())
    print("\n" + "=" * 70)

