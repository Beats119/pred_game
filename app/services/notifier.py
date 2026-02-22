import httpx
from typing import Optional
from app.settings import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

class TelegramNotifier:
    """Send async notifications to Telegram"""
    
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Sends a text message to the configured channel/chat."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                logger.info(f"Notification sent successfully: {text[:30]}...")
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

notifier = TelegramNotifier()
