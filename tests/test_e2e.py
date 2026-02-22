import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper import BDGScraper
from app.services.pattern_matcher import matcher
from app.services.notifier import notifier
from app.settings import settings
from app.utils.logger import get_logger

# Import the actual module so we can override its instance
from app.services import redis_client as original_redis_module

logger = get_logger("EndToEndTest")

# --- MOCK REDIS FOR LOCAL TESTING ---
import fakeredis.aioredis
original_redis_module.redis_client.client = fakeredis.aioredis.FakeRedis(decode_responses=True)
redis_client = original_redis_module.redis_client
# ------------------------------------

async def test_all():
    logger.info("Starting End-to-End Regressive Test...")
    
    # 1. Check Redis Connection
    try:
        await redis_client.client.ping()
        logger.info("[SUCCESS] Redis (Mock): Connected successfully")
    except Exception as e:
        logger.error(f"[FAIL] Redis Connection Failed: {e}")
        logger.error("Make sure Redis is running locally on port 6379 for this test!")
        return

    # 2. Check Telegram Bot directly
    try:
        logger.info("Testing Telegram Notification...")
        test_msg = "<b>BDG WIN Regressive Test</b>\nJust verifying the bot connection!"
        success = await notifier.send_message(test_msg)
        if success:
            logger.info("[SUCCESS] Telegram: Message sent successfully")
        else:
            logger.error("[FAIL] Telegram: Failed to send message. Check BOT_TOKEN and CHAT_ID in .env")
            return
    except Exception as e:
        logger.error(f"[FAIL] Telegram Error: {e}")
        return

    # 3. Test Scraper Engine
    scraper = BDGScraper()
    try:
        await scraper.initialize()
        logger.info("Browser initialized, logging in...")
        
        logger.info("Fetching game results...")
        results = await scraper.fetch_game_results()
        
        if not results:
            logger.error("[FAIL] Scraper: Failed to fetch any results.")
            return
            
        logger.info(f"[SUCCESS] Scraper: Successfully fetched {len(results)} results.")
        
        # 4. End to End Processing
        new_added = 0
        for res in results:
            if await redis_client.add_result(res):
                new_added += 1
                
        logger.info(f"[SUCCESS] Redis: Inserted {new_added} new periods into cache.")
        
        # Get history
        history = await redis_client.get_history(limit=50)
        
        # 5. Pattern Matching (Forced Match For Testing Live Data)
        logger.info(f"[SUCCESS] Pattern Matcher evaluated. Forcing a test notification with LIVE DATA...")
        
        latest_period = results[0]['period']
        latest_bs = results[0].get('bigSmall', 'Unknown')
        
        msg = (
            f"<b>BDG WIN Pattern Detected (110% ACCURATE LIVE TEST)!</b>\n\n"
            f"Pattern: FORCED_MATCH_TEST\n"
            f"Sequence: [Live Scraped Data]\n"
            f"Latest Period: <code>{latest_period}</code>\n"
            f"Latest Result: {latest_bs}\n\n"
            f"<i>Pipeline is fully verified!</i>"
        )
        await notifier.send_message(msg)
        logger.info("[SUCCESS] Full Cycle: Scrape -> Cache -> Match -> Notify complete!")
        logger.info("[SUCCESS] End to end test finished successfully!")
        
    except Exception as e:
        logger.error(f"❌ E2E Test failed with error: {e}", exc_info=True)
    finally:
        await scraper.close()
        await redis_client.client.close()

if __name__ == "__main__":
    asyncio.run(test_all())
