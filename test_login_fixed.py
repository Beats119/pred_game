#!/usr/bin/env python3
"""
Test the fixed login implementation
"""
import asyncio
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.scraper import BDGScraper
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def test_login():
    print("=" * 70)
    print("  TESTING FIXED LOGIN")
    print("=" * 70)
    print()
    
    scraper = BDGScraper()
    
    try:
        print("🌐 Initializing browser and logging in...")
        await scraper.initialize()
        
        if scraper.is_logged_in:
            print("\n✅ LOGIN SUCCESSFUL!")
            
            print("\n🎮 Fetching game results...")
            results = await scraper.fetch_game_results()
            
            if results and len(results) > 0:
                print(f"\n✅ Successfully fetched {len(results)} game results!")
                print("\n" + "=" * 70)
                print(f"{'#':<4} {'Period':<15} {'Number':<8} {'Big/Small':<10}")
                print("=" * 70)
                
                for i, r in enumerate(results[:10]):
                    print(f"{i+1:<4} {r['period']:<15} {r['number']:<8} {r['bigSmall']:<10}")
                
                print("=" * 70)
                
                # Build pattern
                sequence = [r['bigSmall'][0] for r in results]  # B or S
                print(f"\n🎯 CURRENT PATTERN: {'-'.join(sequence[:10])}")
                
            else:
                print("\n⚠️ No results fetched - check extraction logic")
        else:
            print("\n❌ LOGIN FAILED")
            print("Check logs/login_*.png screenshots for debugging")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await scraper.close()
        print("\n✅ Test complete")

if __name__ == "__main__":
    asyncio.run(test_login())
