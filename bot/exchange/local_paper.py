"""
Self-contained local paper exchange for the dashboard.

Simulates realistic market prices with random walks - no external
dependencies (no ccxt, no Binance connection). Implements the same
interface that OrderManager and PortfolioTracker expect.
"""

import random
import time
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# Realistic base prices (approximate April 2026 levels)
_BASE_PRICES = {
    "BTC/USDT": 68500.0,
    "ETH/USDT": 3550.0,
    "SOL/USDT": 148.0,
    "BNB/USDT": 585.0,
    "XRP/USDT": 0.63,
    "DOGE/USDT": 0.167,
    "ADA/USDT": 0.48,
    "AVAX/USDT": 38.5,
}


class LocalPaperExchange:
    """
    Fully offline paper exchange with simulated price movements.
    Prices drift via small random walks on each read, giving the
    dashboard live-updating data without any network calls.
    """

    def __init__(self, initial_balance_usdt: float = 10000.0):
        self.balances: dict[str, float] = {"USDT": initial_balance_usdt}
        self.orders: list[dict] = []
        self._prices: dict[str, float] = dict(_BASE_PRICES)
        self._volatility: dict[str, float] = {
            "BTC/USDT": 0.0008,
            "ETH/USDT": 0.0012,
            "SOL/USDT": 0.0018,
            "BNB/USDT": 0.0010,
            "XRP/USDT": 0.0020,
            "DOGE/USDT": 0.0025,
            "ADA/USDT": 0.0022,
            "AVAX/USDT": 0.0020,
        }
        logger.info(
            "Local paper exchange initialized with $%.2f USDT", initial_balance_usdt
        )

    # ── Price simulation ─────────────────────────────

    def _tick(self, symbol: str) -> float:
        """Advance the price by one random step and return the new price."""
        if symbol not in self._prices:
            raise ValueError(f"Unknown symbol: {symbol}")
        vol = self._volatility.get(symbol, 0.0015)
        change = random.gauss(0.00002, vol)  # tiny upward drift
        self._prices[symbol] *= 1 + change
        return self._prices[symbol]

    # ── Public exchange interface ────────────────────

    def connect(self) -> bool:
        logger.info("Local paper exchange connected (offline mode)")
        return True

    def get_price(self, symbol: str) -> float:
        return self._tick(symbol)

    def get_ticker(self, symbol: str) -> dict:
        price = self._tick(symbol)
        return {
            "symbol": symbol,
            "last": price,
            "bid": price * 0.9999,
            "ask": price * 1.0001,
            "high": price * 1.01,
            "low": price * 0.99,
            "baseVolume": random.uniform(500, 5000),
            "quoteVolume": random.uniform(1e6, 5e7),
            "timestamp": int(time.time() * 1000),
        }

    def get_balance(self) -> dict:
        result = {}
        for currency, total in self.balances.items():
            if total > 0 or currency == "USDT":
                result[currency] = {
                    "free": total,
                    "used": 0.0,
                    "total": total,
                }
        # Always include USDT even if 0
        if "USDT" not in result:
            result["USDT"] = {"free": 0.0, "used": 0.0, "total": 0.0}
        return result

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1h",
        since: Optional[int] = None,
        limit: int = 200,
    ) -> list:
        """Generate synthetic OHLCV bars for chart display."""
        base = self._prices.get(symbol, 100.0)
        vol = self._volatility.get(symbol, 0.0015)
        now_ms = int(time.time() * 1000)
        # Map timeframe to milliseconds
        tf_ms = {"1m": 60_000, "5m": 300_000, "15m": 900_000,
                 "1h": 3_600_000, "4h": 14_400_000, "1d": 86_400_000}
        interval = tf_ms.get(timeframe, 3_600_000)
        bars = []
        price = base * (1 - vol * limit * 0.3)  # start lower for uptrend
        for i in range(limit):
            ts = now_ms - (limit - i) * interval
            open_ = price
            close = open_ * (1 + random.gauss(0.0001, vol))
            high = max(open_, close) * (1 + abs(random.gauss(0, vol * 0.5)))
            low = min(open_, close) * (1 - abs(random.gauss(0, vol * 0.5)))
            volume = random.uniform(50, 500)
            bars.append([ts, open_, high, low, close, volume])
            price = close
        return bars

    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "market",
        amount: float = 0,
        price: Optional[float] = None,
    ) -> dict:
        fill_price = self.get_price(symbol)
        base, quote = symbol.split("/")
        cost = amount * fill_price
        fee = cost * 0.001

        if side == "buy":
            total_cost = cost + fee
            if self.balances.get(quote, 0) < total_cost:
                raise ValueError(
                    f"Insufficient {quote}: need {total_cost:.2f}, "
                    f"have {self.balances.get(quote, 0):.2f}"
                )
            self.balances[quote] = self.balances.get(quote, 0) - total_cost
            self.balances[base] = self.balances.get(base, 0) + amount
        elif side == "sell":
            if self.balances.get(base, 0) < amount:
                raise ValueError(
                    f"Insufficient {base}: need {amount}, "
                    f"have {self.balances.get(base, 0)}"
                )
            self.balances[base] = self.balances.get(base, 0) - amount
            self.balances[quote] = self.balances.get(quote, 0) + (cost - fee)

        order = {
            "id": f"local_{uuid.uuid4().hex[:12]}",
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "filled": amount,
            "price": fill_price,
            "average": fill_price,
            "cost": cost,
            "fee": {"cost": fee, "currency": quote},
            "status": "closed",
            "timestamp": int(time.time() * 1000),
            "datetime": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }
        self.orders.append(order)
        logger.info(
            "[LOCAL] %s %.6f %s @ %.4f  cost=%.2f  fee=%.4f",
            side.upper(), amount, symbol, fill_price, cost, fee,
        )
        return order

    def cancel_order(self, order_id: str, symbol: str) -> dict:
        return {"id": order_id, "status": "canceled"}

    def get_open_orders(self, symbol: Optional[str] = None) -> list:
        return []

    def get_my_trades(self, symbol=None, since=None, limit=100) -> list:
        trades = [o for o in self.orders if o.get("status") == "closed"]
        if symbol:
            trades = [t for t in trades if t["symbol"] == symbol]
        return trades[-limit:]

    def withdraw(self, currency, amount, address, tag=None, params=None):
        bal = self.balances.get(currency, 0)
        if bal < amount:
            raise ValueError(f"Insufficient {currency}")
        self.balances[currency] = bal - amount
        return {"id": f"wd_{uuid.uuid4().hex[:8]}", "status": "ok"}
