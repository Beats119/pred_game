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
        self.context = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        self._cached_results: List[Dict] = []  # populated by background response listener

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
            
            # BDG WIN is a mobile SPA using Vant. It completely changes DOM and network behavior 
            # if user-agent isn't mobile. MUST force mobile viewport even in headless/server.
            self.context = await self.browser.new_context(
                viewport={"width": 414, "height": 896},
                user_agent="Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.144 Mobile Safari/537.36",
                is_mobile=True,
                has_touch=True,
            )
            
            self.page = await self.context.new_page()
            
            # Apply stealth plugin to avoid Cloudflare/Vue headless detection
            try:
                from playwright_stealth import stealth_async
                await stealth_async(self.page)
                logger.info("Playwright stealth plugin applied")
            except ImportError:
                logger.warning("playwright-stealth not installed, bot detection might trigger on server")


            # ── Register persistent network response listener ──
            # Captures game history JSON the moment Vue app fetches it
            # (before login, during home page load, or during WinGo navigation)
            async def _on_response(response):
                url = response.url
                if "GetHistoryIssuePage" in url or ("WinGo_30S" in url and ".json" in url):
                    try:
                        if response.status == 200:
                            import json as _json
                            text = await response.text()
                            data = _json.loads(text)
                            parsed = _parse_api_response(data)
                            if parsed:
                                self._cached_results = parsed
                                logger.info(f"📦 Network listener cached {len(parsed)} results from {url}")
                    except Exception as e:
                        logger.debug(f"Response listener parse error: {e}")

            self.page.on("response", _on_response)
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
        """Fetch WinGo 30S game results. Primary: in-browser fetch(). Fallback: DOM."""

        # ── FALLBACK: Browser navigation + DOM extraction ──
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                if not self.is_logged_in or not self.page or self.page.is_closed():
                    try:
                        if self.page and self.page.is_closed():
                            await self.close()
                            await self.initialize()
                        else:
                            await self.login()
                    except Exception as e:
                        logger.error(f"Failed to establish session: {e}")
                        retry_count += 1
                        continue

                home_url = f"{settings.BDG_BASE_URL.rstrip('/')}/#/home"
                await self.page.goto(home_url, wait_until="domcontentloaded")
                await asyncio.sleep(3)

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
                    logger.warning(f"Lottery fallback: {e}")
                    await self.page.mouse.click(207, 183)

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
                    logger.warning(f"Win Go fallback: {e}")
                    await self.page.mouse.click(207, 430)

                try:
                    await self.page.wait_for_url("**/saasLottery/**", timeout=10000)
                    logger.info(f"WinGo page loaded: {self.page.url}")
                except Exception as e:
                    logger.warning(f"URL wait timeout: {e}")

                # ── PRIMARY: Background Response Listener Cache ──
                logger.info("Waiting for background network listener to capture data (up to 10s)...")
                for _ in range(5):
                    if self._cached_results:
                        logger.info(f"✅ Using {len(self._cached_results)} results captured by background network listener")
                        results = self._cached_results
                        for i, r in enumerate(results[:3]):
                            logger.info(f"   #{i+1}: Period={r.get('period')}, Number={r.get('number')}, BigSmall={r.get('bigSmall')}")
                        # Clear cache so we don't return stale data next poll
                        self._cached_results = []
                        return results
                    await asyncio.sleep(2)

                # ── SECONDARY: Vue Component Direct Data Extraction ──
                # If network listener missed it, extract directly from Vue's reactive state
                logger.info("Background cache empty, attempting direct Vue component state extraction...")
                try:
                    # Explicitly wait for the list container to mount
                    await self.page.wait_for_selector('.record-list, .van-list', timeout=10000)
                    
                    # Try extracting state a few times (Vue might take a moment to populate arrays)
                    for wait_attempt in range(5):
                        data = await self.page.evaluate("""
                            () => {
                                // Find the container element that might hold Vue data
                                const container = document.querySelector('.record-list') || document.querySelector('.van-list');
                                if (!container) return null;
                                
                                // Access Vue 3 internal instance proxy if available
                                let records = [];
                                try {
                                    const vueApp = document.querySelector('#app')?.__vue_app__;
                                    // In Vue 3, __vueParentComponent is often attached to elements
                                    const comp = container.__vueParentComponent;
                                    if (comp && comp.ctx && comp.ctx.gameRecords) {
                                        records = comp.ctx.gameRecords;
                                    } else if (comp && comp.proxy && comp.proxy.gameRecords) {
                                        records = comp.proxy.gameRecords;
                                    }
                                } catch(e) {}
                                
                                return { records: records };
                            }
                        """)
                        if data and data.get("records") and len(data["records"]) > 0:
                            logger.info("✅ Successfully extracted game records directly from Vue state")
                            results = _parse_api_response({"list": data["records"]})
                            if results:
                                return results
                        
                        logger.debug("Vue state empty, waiting 2s...")
                        await asyncio.sleep(2)
                        
                except Exception as e:
                    logger.warning(f"Vue component extraction failed: {e}")
                    try:
                        # Dump what the server actually sees for debugging
                        logger.warning(f"Failed on URL: {self.page.url}")
                        dom_preview = await self.page.evaluate("document.body.innerHTML")
                        logger.warning(f"Current DOM preview (first 1000 chars): {dom_preview[:1000]}")
                        
                        # Take base64 screenshot and log it (so we can decode it locally from Railway logs)
                        screenshot_bytes = await self.page.screenshot(type="jpeg", quality=30)
                        import base64
                        b64 = base64.b64encode(screenshot_bytes).decode('ascii')
                        logger.warning(f"DEBUG_SCREENSHOT_B64: {b64}")
                    except Exception as dbg_err:
                        logger.error(f"Failed to capture debug DOM/screenshot: {dbg_err}")

                # ── DOM FALLBACK ──
                logger.info("Falling back to DOM extraction...")
                await asyncio.sleep(5)
                for i in range(5):
                    await self.page.mouse.wheel(0, 700)
                    await asyncio.sleep(1.5)

                results = await self._extract_results()
                if not results:
                    raise Exception("No results extracted")
                return results

            except Exception as e:
                logger.error(f"Fetch attempt {retry_count + 1} failed: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    logger.error("Max retries reached")
                    return []
                await asyncio.sleep(5)

        return []



    async def _extract_results(self) -> List[Dict]:
        """DOM fallback: extract game results from .van-row elements."""
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
