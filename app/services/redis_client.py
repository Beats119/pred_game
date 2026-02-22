import redis.asyncio as redis
import json
from typing import List, Dict, Optional
from app.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.history_key = "bdg:history"
        self.notified_key = "bdg:notified_patterns"

    async def add_result(self, result: Dict) -> bool:
        """
        Adds a single game result. 
        Returns True if it was added (new period), False if already exists.
        """
        period = result.get("period")
        
        # Check if already in history by checking the latest elements
        recent = await self.get_history(10)
        if any(r.get("period") == period for r in recent):
            return False

        # Add to history
        await self.client.lpush(self.history_key, json.dumps(result))
        
        # Trim history to HISTORY_SIZE
        await self.client.ltrim(self.history_key, 0, settings.HISTORY_SIZE - 1)
        return True

    async def get_history(self, limit: int = 50) -> List[Dict]:
        """Returns the most recent game results."""
        results_str = await self.client.lrange(self.history_key, 0, limit - 1)
        return [json.loads(r) for r in results_str]

    async def is_pattern_notified(self, period: str, pattern_name: str) -> bool:
        """
        Check if a notification was already sent for a specific period and pattern.
        """
        key = f"{self.notified_key}:{period}:{pattern_name}"
        exists = await self.client.exists(key)
        if not exists:
            # Set with expiration (e.g., 2 hours) to avoid memory leaks
            await self.client.setex(key, 7200, "1")
            return False
        return True

redis_client = RedisClient()
