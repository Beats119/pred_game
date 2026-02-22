import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # BDG WIN Config
    BDG_USERNAME: str
    BDG_PASSWORD: str
    BDG_BASE_URL: str = "https://bdgwina.cc"
    BDG_GAME_URL: str = "https://bdgwina.cc/#/saasLottery/WinGo?gameCode=WinGo_30S&lottery=WinGo"

    # Redis Config
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Application Settings
    POLL_INTERVAL: int = 30
    HISTORY_SIZE: int = 50
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# Instantiate settings globally
settings = Settings()
