"""
config.py — Centralized settings for Bitcoin Investment AI
Loads from .env file automatically
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Hata API
    hata_api_key: str = ""
    hata_api_secret: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Bot Strategy
    daily_amount_myr: float = 5.0          # RM per hari
    buy_threshold_pct: float = 1.5         # % jatuh sebelum beli
    sell_threshold_pct: float = 2.0        # % naik sebelum jual
    rsi_oversold: int = 30
    rsi_overbought: int = 70
    schedule_time: str = "08:00"           # 24h format
    max_capital_myr: float = 100.0
    bot_enabled: bool = True
    supported_coins: list = ["BTC", "ETH", "SOL", "XRP", "LTC"]

    # Database
    database_url: str = "sqlite:///./investment_ai.db"

    # Server
    backend_port: int = 8000
    frontend_port: int = 3000

    model_config = {"env_file": "../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
