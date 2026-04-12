"""
strategy/signal_engine.py — Technical Analysis & AI Signal Generator
Calculates RSI, EMA, and generates BUY/SELL/HOLD signals
"""
import pandas as pd
import pandas_ta as ta
from loguru import logger
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta
import sys, os
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


@dataclass
class Signal:
    """Output dari signal engine"""
    action: str                # "BUY" | "SELL" | "HOLD"
    reason: str                # kenapa bot buat keputusan ni
    confidence: float          # 0.0 - 1.0
    current_price: float
    price_change_pct: float    # perubahan dari semalam (%)
    rsi: Optional[float]
    ema_20: Optional[float]
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class SignalEngine:
    """
    Analisis teknikal untuk generate buy/sell signal
    
    Logic:
    - BUY bila: harga jatuh >= threshold% ATAU RSI < 30
    - SELL bila: harga naik >= threshold% DAN RSI > 50
    - HOLD: semua lain
    """

    def __init__(self):
        self.price_history: List[float] = []
        self.timestamps: List[datetime] = []
        self._bootstrap_historical_data()

    def _bootstrap_historical_data(self):
        """Ambil data harga 30 hari lepas dari CoinGecko (percuma) untuk bootstrap RSI"""
        try:
            logger.info("⏳ Memuat turun historical BTC prices dari CoinGecko...")
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=myr&days=30&interval=daily"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                prices = resp.json().get("prices", [])
                for item in prices:
                    # item[0] = timestamp (ms), item[1] = price
                    dt = datetime.fromtimestamp(item[0] / 1000.0)
                    self.price_history.append(float(item[1]))
                    self.timestamps.append(dt)
                logger.success(f"✅ Berjaya bootstrap {len(self.price_history)} hari historical prices.")
            else:
                logger.warning(f"⚠️ Gagal fetch historical data dari CoinGecko: {resp.status_code}")
        except Exception as e:
            logger.error(f"❌ Error bootstrapping historical data: {e}")

    def add_price(self, price: float, timestamp: Optional[datetime] = None):
        """Add harga baru ke historical data"""
        self.price_history.append(price)
        self.timestamps.append(timestamp or datetime.now())
        # Keep last 100 prices
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
            self.timestamps = self.timestamps[-100:]

    def calculate_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)"""
        try:
            if len(prices) < period + 1:
                logger.warning(f"⚠️ Not enough data for RSI (need {period+1}, got {len(prices)})")
                return None

            df = pd.DataFrame({"close": prices})
            rsi_series = ta.rsi(df["close"], length=period)
            if rsi_series is not None and len(rsi_series) > 0:
                rsi_val = rsi_series.iloc[-1]
                return round(float(rsi_val), 2) if not pd.isna(rsi_val) else None
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
        return None

    def calculate_ema(self, prices: List[float], period: int = 20) -> Optional[float]:
        """Calculate EMA (Exponential Moving Average)"""
        try:
            if len(prices) < period:
                return None
            df = pd.DataFrame({"close": prices})
            ema_series = ta.ema(df["close"], length=period)
            if ema_series is not None and len(ema_series) > 0:
                ema_val = ema_series.iloc[-1]
                return round(float(ema_val), 2) if not pd.isna(ema_val) else None
        except Exception as e:
            logger.error(f"Error calculating EMA: {e}")
        return None

    def calculate_price_change(self, current_price: float, prev_price: float) -> float:
        """Kira % perubahan harga"""
        if prev_price == 0:
            return 0.0
        return round(((current_price - prev_price) / prev_price) * 100, 4)

    def generate_signal(
        self,
        current_price: float,
        prev_price: float,
        price_history: Optional[List[float]] = None,
        has_btc: bool = False,
        btc_avg_cost: Optional[float] = None,
    ) -> Signal:
        """
        Generate buy/sell/hold signal berdasarkan:
        - % perubahan harga dari semalam
        - RSI indicator
        - EMA trend
        """
        prices = price_history or self.price_history
        prices_with_current = prices + [current_price]

        # Calculate indicators
        price_change_pct = self.calculate_price_change(current_price, prev_price)
        rsi = self.calculate_rsi(prices_with_current)
        ema_20 = self.calculate_ema(prices_with_current)

        logger.info(f"""
📊 Signal Analysis:
   Harga semasa:  RM {current_price:,.2f}
   Perubahan:     {price_change_pct:+.2f}%
   RSI:           {rsi}
   EMA20:         {ema_20}
   Ada BTC:       {has_btc}
        """)

        # =====================
        # DAILY TREND FLIPPER 
        # (Execute Buy/Sell blindly based on simple trend)
        # =====================
        
        # Jika hari ini lebih tinggi atau sama dengan semalam -> SELL
        if price_change_pct > 0:
            return Signal(
                action="SELL",
                reason=f"Harga NAIK sebanyak {price_change_pct:+.2f}% dari semalam. Tembak Sell!",
                confidence=1.0,
                current_price=current_price,
                price_change_pct=price_change_pct,
                rsi=rsi,
                ema_20=ema_20
            )
            
        # Jika hari ini lebih rendah dari semalam -> BUY
        elif price_change_pct < 0:
            return Signal(
                action="BUY",
                reason=f"Harga JATUH sebanyak {price_change_pct:+.2f}% dari semalam. Tembak Buy!",
                confidence=1.0,
                current_price=current_price,
                price_change_pct=price_change_pct,
                rsi=rsi,
                ema_20=ema_20
            )
            
        # Jika harga statik 0.00% (sangat jarang)
        return Signal(
            action="HOLD",
            reason=f"Harga statik 0%.",
            confidence=1.0,
            current_price=current_price,
            price_change_pct=price_change_pct,
            rsi=rsi,
            ema_20=ema_20
        )


# Singleton
signal_engine = SignalEngine()
