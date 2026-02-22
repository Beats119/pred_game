import asyncio
from typing import List, Dict
from app.services.scraper import BDGScraper
from app.services.redis_client import redis_client
from app.services.pattern_matcher import matcher
from app.services.notifier import notifier
from app.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def poll_task():
    """Background task to fetch, match and notify every POLL_INTERVAL."""
    scraper = BDGScraper()
    await scraper.initialize()
    
    try:
        while True:
            logger.info("Fetching latest results...")
            results = await scraper.fetch_game_results()
            
            if results:
                # Add to history, True if it's a new result
                new_results_added = False
                for res in results:
                    added = await redis_client.add_result(res)
                    if added:
                        new_results_added = True

                if new_results_added:
                    # Get updated history
                    history = await redis_client.get_history(limit=settings.HISTORY_SIZE)
                    
                    # Pattern Match
                    match = matcher.analyze_history(history)
                    if match:
                        pattern_name, sequence, period = match
                        
                        # Check if already notified
                        already_notified = await redis_client.is_pattern_notified(period, pattern_name)
                        
                        if not already_notified:
                            logger.info(f"🚨 Pattern Detected: {pattern_name} in period {period}")
                            
                            # Build last 10 sequence for display
                            last_10 = history[:10]
                            live_seq = " → ".join(
                                ["🔴 Big" if (r.get("bigSmall","").lower()=="big") else "🔵 Small"
                                 for r in last_10]
                            )
                            
                            msg = (
                                f"🎯 <b>BDG WIN Pattern Detected!</b>\n\n"
                                f"📝 <b>Pattern:</b> {pattern_name}\n"
                                f"🔍 <b>Sequence (newest→oldest):</b>\n{sequence}\n\n"
                                f"📊 <b>Live Last 10:</b>\n{live_seq}\n\n"
                                f"⏰ <b>Latest Period:</b> <code>{period}</code>\n\n"
                                f"<i>💡 Pattern detected — place your bet!</i>"
                            )
                            await notifier.send_message(msg)
                        else:
                            logger.debug(f"Already notified for {pattern_name} in {period}")
                else:
                    logger.debug("No new results to process.")
            
            # Wait for next poll
            await asyncio.sleep(settings.POLL_INTERVAL)
            
    except Exception as e:
        logger.error(f"Error in background task: {e}")
    finally:
        await scraper.close()

def run_scheduler_in_background():
    """Fire and forget the asyncio polling task"""
    asyncio.create_task(poll_task())
