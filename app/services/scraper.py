import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Browser, Page
from app.settings import settings
from app.utils.logger import get_logger
import os

logger = get_logger(__name__)

class BDGScraper:
    """Scrape BDG WIN game results using Playwright"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
    
    async def initialize(self):
        """Initialize browser and login"""
        try:
            playwright = await async_playwright().start()
            # headless=True on server (Railway/Render), False only for local debug
            headless = os.getenv("HEADLESS", "true").lower() != "false"
            self.browser = await playwright.chromium.launch(
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--disable-gpu',       # required for Docker/server
                    '--no-zygote',         # required for Docker/server
                ]
            )
            
            # Use desktop viewport in headless/server mode, mobile for local dev
            if headless:
                self.context = await self.browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                )
            else:
                self.context = await self.browser.new_context(
                    viewport={"width": 414, "height": 896},
                    user_agent="Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
                    is_mobile=True,
                    has_touch=True,
                )
            
            self.page = await self.context.new_page()
            
            logger.info("Browser initialized successfully")
            await self.login()
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def login(self):
        """Login to BDG WIN with retry logic - handles Vue.js SPA"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                login_url = f"{settings.BDG_BASE_URL.rstrip('/')}/#/login"
                logger.info(f"Attempting login to {login_url} (attempt {retry_count + 1}/{max_retries})...")
                
                # Go to login page directly
                await self.page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
                logger.info("Login page loaded, waiting for Vue.js to render...")
                await asyncio.sleep(5)  # Give Vue time to render
                
                # Wait for login form inputs to appear
                logger.info("Waiting for login form inputs...")
                try:
                    await self.page.wait_for_selector('input[type="tel"], input[type="text"], input[placeholder*="phone"], input[placeholder*="Phone"], input[name="username"]', timeout=10000)
                    logger.info("Login form inputs detected")
                except Exception as e:
                    logger.warning(f"Login form not found, reloading page: {e}")
                    await self.page.reload(wait_until="domcontentloaded")
                    await asyncio.sleep(5)  # Wait after reload
                    # Second attempt
                    try:
                        await self.page.wait_for_selector('input[type="tel"], input[type="text"], input[placeholder*="phone"], input[placeholder*="Phone"], input[name="username"]', timeout=10000)
                        logger.info("Login form inputs detected (after reload)")
                    except Exception as e2:
                        raise Exception(f"Login form not found even after reload: {e2}")
                
                await asyncio.sleep(2)
                
                # Fill username/phone
                username_filled = False
                username_selectors = [
                    'input[type="tel"]',
                    'input[type="text"]',
                    'input[placeholder*="phone"]',
                    'input[placeholder*="Phone"]',
                    'input[name="username"]',
                    'input[name="phone"]',
                    'input[name="account"]'
                ]
                
                for sel in username_selectors:
                    try:
                        elem = await self.page.query_selector(sel)
                        if elem:
                            # Check if visible
                            is_visible = await elem.is_visible()
                            if is_visible:
                                logger.info(f"Filling username with selector: {sel}")
                                await elem.click()
                                await asyncio.sleep(0.5)
                                await self.page.keyboard.type(settings.BDG_USERNAME, delay=100)
                                username_filled = True
                                break
                    except:
                        continue
                        
                if not username_filled:
                    raise Exception("Username field not found or not visible")
                
                await asyncio.sleep(1)
                
                # Fill password
                password_filled = False
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[placeholder*="password"]',
                    'input[placeholder*="Password"]'
                ]
                
                for sel in password_selectors:
                    try:
                        elem = await self.page.query_selector(sel)
                        if elem:
                            is_visible = await elem.is_visible()
                            if is_visible:
                                logger.info(f"Filling password with selector: {sel}")
                                await elem.click()
                                await asyncio.sleep(0.5)
                                await self.page.keyboard.type(settings.BDG_PASSWORD, delay=100)
                                password_filled = True
                                break
                    except:
                        continue
                        
                if not password_filled:
                    raise Exception("Password field not found or not visible")
                
                await asyncio.sleep(1)
                
                # Click login button
                button_clicked = False
                button_selectors = [
                    'button[type="submit"]',
                    'button:has-text("Login")',
                    'button:has-text("Sign In")',
                    'button:has-text("Log In")',
                    '[class*="login-btn"]',
                    '[class*="loginBtn"]',
                    'button[class*="submit"]',
                    'button[class*="btn"]'
                ]
                
                for sel in button_selectors:
                    try:
                        elem = await self.page.query_selector(sel)
                        if elem:
                            is_visible = await elem.is_visible()
                            if is_visible:
                                logger.info(f"Clicking login button: {sel}")
                                await elem.click()
                                button_clicked = True
                                break
                    except:
                        continue
                        
                if not button_clicked:
                    raise Exception("Login button not found or not visible")
                
                # Wait for navigation after login
                logger.info("Waiting for login to complete...")
                await asyncio.sleep(5)
                
                # Check if login was successful
                current_url = self.page.url
                logger.info(f"After login URL: {current_url}")
                
                # If still on login page, login failed
                if "login" in current_url.lower():
                    raise Exception("Still on login page after clicking login button")
                
                self.is_logged_in = True
                logger.info("✅ Successfully logged in to BDG WIN")
                return
                
            except Exception as e:
                logger.error(f"Login attempt {retry_count + 1} failed: {e}")
                self.is_logged_in = False
                retry_count += 1
                if retry_count < max_retries:
                    logger.info(f"Retrying in 5 seconds...")
                    await asyncio.sleep(5)
                else:
                    raise Exception(f"Failed to login after {max_retries} attempts: {e}")

    async def fetch_game_results(self) -> List[Dict]:
        """Fetch WinGo 30S game results recently emitted."""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                if not self.is_logged_in or not self.page or self.page.is_closed():
                    try:
                        if self.page and self.page.is_closed():
                            logger.info("Browser page was closed/crashed. Re-initializing entirely...")
                            await self.close()
                            await self.initialize()
                        else:
                            await self.login()
                    except Exception as e:
                        logger.error(f"Failed to establish session: {e}")
                        retry_count += 1
                        continue
                
                # ── APPROACH: Intercept the API response the Vue app fetches ──
                # Vue's virtual scroll never renders DOM rows in headless mode.
                # Instead we capture the JSON the app fetches from its backend.
                captured_results = []
                api_event = asyncio.Event()

                async def handle_response(response):
                    """Capture game history API responses."""
                    url = response.url
                    # Exact confirmed BDG WIN history endpoint (captured via network inspection)
                    is_history = (
                        "GetHistoryIssuePage" in url or
                        "GetNoaverageEmerdList" in url or
                        ("WinGo_30S" in url and (".json" in url or "history" in url.lower())) or
                        any(k in url for k in ["lotteryHistory", "gameRecord", "result/list"])
                    )
                    if is_history:
                        try:
                            if response.status == 200:
                                data = await response.json()
                                logger.info(f"🌐 API intercepted: {url}")
                                logger.info(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                                parsed = _parse_api_response(data)
                                if parsed:
                                    captured_results.extend(parsed)
                                    api_event.set()
                        except Exception as e:
                            logger.debug(f"Could not parse response from {url}: {e}")

                self.page.on("response", handle_response)

                # 1. Navigate to Home then click through to WinGo
                home_url = f"{settings.BDG_BASE_URL.rstrip('/')}/#/home"
                await self.page.goto(home_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

                # 2. Click Lottery tab
                logger.info("Clicking Lottery tab...")
                try:
                    lottery_box = await self.page.locator('text="Lottery"').first.bounding_box(timeout=8000)
                    if lottery_box:
                        cx = lottery_box['x'] + lottery_box['width'] / 2
                        cy = lottery_box['y'] + lottery_box['height'] / 2
                        await self.page.mouse.click(cx, cy)
                        logger.info(f"Lottery clicked at ({cx:.0f}, {cy:.0f})")
                    else:
                        raise Exception("no box")
                except Exception as e:
                    logger.warning(f"Lottery fallback coord click: {e}")
                    await self.page.mouse.click(207, 183)

                # 3. Wait for Win Go card and click it
                logger.info("Waiting for Win Go card to render...")
                try:
                    await self.page.wait_for_selector('text="Win Go"', timeout=10000)
                    logger.info("Win Go card found in DOM")
                except Exception as e:
                    logger.warning(f"Win Go card not found: {e}")

                await asyncio.sleep(1)
                logger.info("Clicking Win Go card...")
                try:
                    wingo_box = await self.page.locator('text="Win Go"').first.bounding_box(timeout=8000)
                    if wingo_box:
                        cx = wingo_box['x'] + wingo_box['width'] / 2
                        cy = wingo_box['y'] + wingo_box['height'] / 2
                        await self.page.mouse.click(cx, cy)
                        logger.info(f"Win Go clicked at ({cx:.0f}, {cy:.0f})")
                    else:
                        raise Exception("no box")
                except Exception as e:
                    logger.warning(f"Win Go fallback coord click at (207, 430): {e}")
                    await self.page.mouse.click(207, 430)

                # 4. Wait for URL change
                logger.info("Waiting for WinGo page to load...")
                try:
                    await self.page.wait_for_url("**/saasLottery/**", timeout=10000)
                    logger.info(f"WinGo page loaded: {self.page.url}")
                except Exception as e:
                    logger.warning(f"URL wait timeout: {e}")

                # 5. Wait for API response to be captured (up to 15s)
                logger.info("Waiting for game history API response...")
                try:
                    await asyncio.wait_for(api_event.wait(), timeout=15)
                    logger.info(f"✅ API interception captured {len(captured_results)} results")
                except asyncio.TimeoutError:
                    logger.warning("⚠️ API interception timed out — falling back to DOM extraction")

                # Remove listener
                self.page.remove_listener("response", handle_response)

                # 6. If API gave us data, use it
                if captured_results:
                    results = captured_results[:10]  # newest 10
                    for i, r in enumerate(results[:3]):
                        logger.info(f"   #{i+1}: Period={r.get('period')}, Number={r.get('number')}, BigSmall={r.get('bigSmall')}")
                    return results

                # 7. Fallback: DOM extraction with extra scrolling
                logger.info("Falling back to DOM extraction...")
                await asyncio.sleep(5)
                for i in range(5):
                    await self.page.mouse.wheel(0, 700)
                    await asyncio.sleep(1.5)
                results = await self._extract_results()

                if not results:
                    raise Exception("No results extracted via API or DOM")

                logger.debug(f"Fetched {len(results)} game results")
                return results

            except Exception as e:
                logger.error(f"Fetch attempt {retry_count + 1} failed: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Max retries fetching results reached")
                    return []
                await asyncio.sleep(5)

        return []


def _parse_api_response(data: dict) -> list:
    """Parse BDG WIN game history API response into our standard format."""
    results = []
    try:
        # Try common response structures
        records = None
        if isinstance(data, dict):
            # Common patterns: data.data, data.list, data.result, data.records
            for key in ["data", "list", "result", "records", "rows", "gameRecords"]:
                val = data.get(key)
                if isinstance(val, list) and val:
                    records = val
                    break
                elif isinstance(val, dict):
                    # nested: data.data.list
                    for inner_key in ["list", "records", "rows", "gameRecords"]:
                        inner = val.get(inner_key)
                        if isinstance(inner, list) and inner:
                            records = inner
                            break
                    if records:
                        break
        elif isinstance(data, list):
            records = data

        if not records:
            return []

        for item in records[:10]:
            if not isinstance(item, dict):
                continue
            # Extract period
            period = str(item.get("issueNumber") or item.get("period") or
                        item.get("issue") or item.get("gameNo") or "")
            # Extract number
            number_raw = item.get("number") or item.get("winNumber") or item.get("openCode") or ""
            try:
                number = int(str(number_raw).strip().split(",")[0])
            except (ValueError, TypeError):
                continue
            # Derive Big/Small
            big_small = item.get("bigSmall") or item.get("bigOrSmall") or (
                "Big" if number >= 5 else "Small"
            )
            if period and 0 <= number <= 9:
                results.append({
                    "period": period,
                    "number": number,
                    "bigSmall": big_small,
                    "timestamp": item.get("createTime", 0)
                })
    except Exception as e:
        pass
    return results


    async def _extract_results(self) -> List[Dict]:
        """Extract game results focusing on the accurate Big/Small and Period columns"""
        try:
            
            logger.info("Scrolling down to trigger lazy-loaded game grid...")
            # Scroll down multiple times to ensure the Vue grid renders
            for _ in range(3):
                await self.page.mouse.wheel(0, 800)
                await asyncio.sleep(1)
            
            # Wait explicitly for the rows to render
            await self.page.wait_for_selector('.van-row', timeout=15000)
        except Exception as e:
            logger.warning(f"Timeout waiting for .van-row elements or killing popups: {e}")
            
        await asyncio.sleep(2) # Give it an extra moment to populate text
        
        try:
            results_data = await self.page.evaluate("""
                () => {
                    const results = [];
                    const rows = document.querySelectorAll('.van-row');
                    rows.forEach(row => {
                        if (results.length >= 50) return;
                        
                        const periodCol = row.querySelector('.van-col--10');
                        const numCol = row.querySelector('.record-body-num');
                        const bsCols = row.querySelectorAll('.van-col--5');
                        
                        if (periodCol && numCol && bsCols.length >= 2) {
                            const period = periodCol.innerText.trim();
                            const numberText = numCol.innerText.trim();
                            const bsText = bsCols[1].innerText.trim();
                            
                            if (/^\\d{10,}$/.test(period) && /^\\d$/.test(numberText)) {
                                results.push({
                                    period: period,
                                    number: parseInt(numberText),
                                    bigSmall: bsText,
                                    timestamp: Date.now()
                                });
                            }
                        }
                    });
                    return results;
                }
            """)
            
            if results_data and len(results_data) > 0:
                logger.info(f"✅ Extracted {len(results_data)} results with Big/Small data")
                # Log first 3 for verification
                for i, r in enumerate(results_data[:3]):
                    logger.info(f"   #{i+1}: Period={r['period']}, Number={r['number']}, BigSmall={r.get('bigSmall', '?')}")
                return results_data
            else:
                logger.warning("❌ No Big/Small data extracted from page")
                return []
                
        except Exception as e:
            logger.error(f"DOM extraction failed: {e}")
            return []

    async def close(self):
        """Cleanup playwright resources."""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")
