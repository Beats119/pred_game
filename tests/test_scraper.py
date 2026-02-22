import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.scraper import BDGScraper
from app.utils.logger import get_logger

logger = get_logger("TestScraper")

async def test():
    logger.info("Starting Scraper Test...")
    scraper = BDGScraper()
    
    try:
        await scraper.initialize()
        logger.info("Browser initialized, logging in...")
        
        # Test fetching game results 1 time
        logger.info("Fetching game results...")
        results = await scraper.fetch_game_results()
        
        if results:
            logger.info("Test Success! Scraped output:")
            for r in results[:5]:
                logger.info(f"Period: {r['period']}, Number: {r['number']}, Big/Small: {r['bigSmall']}")
        else:
            logger.warning("Test completed but returned NO results.")
            
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
    finally:
        await scraper.close()
        logger.info("Test finished.")

if __name__ == "__main__":
    asyncio.run(test())
