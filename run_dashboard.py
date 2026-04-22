#!/usr/bin/env python3
"""
Standalone dashboard launcher.

Boots a fully functional trading dashboard in paper or live mode.

Usage:
    python run_dashboard.py                        # paper mode (default)
    python run_dashboard.py --mode live             # LIVE trading (real money!)
    python run_dashboard.py --mode live --testnet   # Binance testnet
    python run_dashboard.py --port 3000             # custom port

Paper mode needs no external dependencies.
Live mode requires BINANCE_API_KEY and BINANCE_API_SECRET in your .env file.

Open http://localhost:8080 in your browser.
"""

import argparse
import logging
import os
import random
import sys
import threading
import time
from datetime import datetime, timedelta

# ── Setup path + logging ─────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("dashboard")

# Silence noisy libs
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

from bot.database.db import init_db, get_session  # noqa: E402
from bot.database.models import Trade, Position, Signal, PortfolioSnapshot, CopyLeader  # noqa: E402
from bot.exchange.local_paper import LocalPaperExchange  # noqa: E402
from bot.exchange.order_manager import OrderManager  # noqa: E402
from bot.risk.manager import RiskManager  # noqa: E402
from bot.portfolio.tracker import PortfolioTracker  # noqa: E402
from bot.dashboard.app import create_dashboard  # noqa: E402


# ═══════════════════════════════════════════════════════
#  Data seeding — creates realistic history for charts
# ═══════════════════════════════════════════════════════

SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
STRATEGIES = ["ai", "copy", "signal", "manual"]


def seed_database(exchange: LocalPaperExchange):
    """Populate the database with realistic historical data."""
    session = get_session()
    now = datetime.utcnow()

    # ── 1.  Portfolio snapshots (30 days) for equity chart ──
    balance = 10000.0
    for days_ago in range(30, -1, -1):
        ts = now - timedelta(days=days_ago, hours=random.randint(0, 6))
        daily_change = random.gauss(25, 60)
        balance = max(balance + daily_change, 8000)
        snap = PortfolioSnapshot(
            total_balance=balance,
            available_balance=balance * random.uniform(0.55, 0.80),
            in_positions=balance * random.uniform(0.20, 0.45),
            total_pnl=balance - 10000,
            daily_pnl=daily_change,
            unrealized_pnl=random.uniform(-30, 50),
            num_open_positions=random.randint(1, 4),
        )
        snap.timestamp = ts
        session.add(snap)

    # ── 2.  Historical trades ──
    trade_data = [
        ("BTC/USDT", "buy",  0.014,  67800, "ai",     18.50, 5),
        ("ETH/USDT", "buy",  0.45,   3480,  "signal", None,  4),
        ("SOL/USDT", "sell", 1.8,    151,   "copy",   -5.40, 3),
        ("BNB/USDT", "buy",  1.2,    578,   "manual", -9.80, 8),
        ("XRP/USDT", "sell", 450,    0.64,  "ai",     12.30, 24),
        ("BTC/USDT", "sell", 0.01,   68900, "ai",     28.00, 48),
        ("ETH/USDT", "sell", 0.30,   3560,  "copy",   8.40,  56),
        ("SOL/USDT", "buy",  3.0,    144,   "signal", -3.20, 72),
        ("BNB/USDT", "sell", 0.8,    590,   "ai",     6.10,  96),
        ("DOGE/USDT", "buy",  1500,   0.168, "signal", -7.50, 120),
        ("BTC/USDT", "buy",  0.005,  67200, "copy",   4.60,  144),
        ("ETH/USDT", "buy",  0.20,   3420,  "manual", 11.30, 168),
    ]

    for sym, side, amt, price, strat, pnl, hours_ago in trade_data:
        t = Trade(
            symbol=sym, side=side, amount=amt,
            price=float(price), average_price=float(price),
            cost=amt * float(price),
            fee=amt * float(price) * 0.001,
            fee_currency="USDT",
            strategy=strat,
            order_id=f"hist-{sym.replace('/', '')}-{side}-{hours_ago}",
            status="filled",
            pnl=pnl,
            is_paper=True,
        )
        t.created_at = now - timedelta(hours=hours_ago)
        session.add(t)

    # ── 3.  Open positions ──
    positions = [
        Position(
            symbol="BTC/USDT", side="long",
            entry_price=67500.0, amount=0.015,
            current_price=exchange.get_price("BTC/USDT"),
            unrealized_pnl=0,
            stop_loss=65500.0, take_profit=72000.0,
            strategy="ai", is_paper=True, is_open=True,
        ),
        Position(
            symbol="ETH/USDT", side="long",
            entry_price=3450.0, amount=0.5,
            current_price=exchange.get_price("ETH/USDT"),
            unrealized_pnl=0,
            stop_loss=3250.0, take_profit=3900.0,
            strategy="signal", is_paper=True, is_open=True,
        ),
        Position(
            symbol="SOL/USDT", side="short",
            entry_price=152.0, amount=2.5,
            current_price=exchange.get_price("SOL/USDT"),
            unrealized_pnl=0,
            stop_loss=160.0, take_profit=135.0,
            strategy="copy", is_paper=True, is_open=True,
        ),
    ]
    for p in positions:
        if p.side == "long":
            p.unrealized_pnl = (p.current_price - p.entry_price) * p.amount
        else:
            p.unrealized_pnl = (p.entry_price - p.current_price) * p.amount
        session.add(p)

    # ── 4.  AI signals ──
    for i in range(15):
        sym = random.choice(SYMBOLS)
        action = random.choice(["buy", "sell", "hold"])
        conf = random.uniform(0.45, 0.95)
        s = Signal(
            source="ai", symbol=sym, timeframe="1h",
            action=action, confidence=conf,
            ta_score=random.uniform(-1, 1),
            ml_score=random.uniform(-1, 1),
            acted_on=(action != "hold" and conf > 0.7),
        )
        s.created_at = now - timedelta(hours=i * 4 + random.randint(0, 3))
        session.add(s)

    # ── 5.  Copy leaders ──
    leaders = [
        CopyLeader(external_id="whale_alpha", label="Whale Alpha",
                   allocation_pct=0.15, is_active=True,
                   total_pnl=42.30, num_trades_copied=6),
        CopyLeader(external_id="degen_king", label="DegenKing",
                   allocation_pct=0.10, is_active=True,
                   total_pnl=-8.10, num_trades_copied=3),
    ]
    for ldr in leaders:
        session.add(ldr)

    session.commit()
    session.close()
    logger.info("Database seeded with historical data")


# ═══════════════════════════════════════════════════════
#  Lightweight strategy wrappers (use real DB queries)
# ═══════════════════════════════════════════════════════

class DashboardStrategy:
    """Minimal strategy wrapper for the dashboard."""
    def __init__(self, name: str, active: bool = True):
        self.name = name
        self.is_active = active
        self._signal_queue = []

    def start(self):
        self.is_active = True

    def stop(self):
        self.is_active = False

    def run(self):
        return []

    def get_status(self) -> dict:
        session = get_session()
        try:
            total_trades = session.query(Trade).filter_by(strategy=self.name).count()
            total_pnl = sum(
                t.pnl or 0
                for t in session.query(Trade)
                .filter_by(strategy=self.name)
                .filter(Trade.pnl.isnot(None))
                .all()
            )
            return {
                "strategy": self.name,
                "is_active": self.is_active,
                "total_trades": total_trades,
                "total_pnl": total_pnl,
            }
        finally:
            session.close()

    def get_latest_signals(self) -> list:
        session = get_session()
        try:
            signals = (
                session.query(Signal)
                .filter_by(source="ai")
                .order_by(Signal.created_at.desc())
                .limit(20)
                .all()
            )
            return [
                {
                    "id": s.id,
                    "symbol": s.symbol,
                    "timeframe": s.timeframe,
                    "action": s.action,
                    "confidence": s.confidence,
                    "ta_score": s.ta_score,
                    "ml_score": s.ml_score,
                    "acted_on": s.acted_on,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                }
                for s in signals
            ]
        finally:
            session.close()

    def get_leaders(self) -> list:
        session = get_session()
        try:
            leaders = session.query(CopyLeader).all()
            return [
                {
                    "id": ldr.id,
                    "external_id": ldr.external_id,
                    "label": ldr.label,
                    "allocation_pct": ldr.allocation_pct,
                    "is_active": ldr.is_active,
                    "total_pnl": ldr.total_pnl,
                    "num_trades": ldr.num_trades_copied,
                    "last_polled": ldr.last_polled_at.isoformat() if ldr.last_polled_at else None,
                }
                for ldr in leaders
            ]
        finally:
            session.close()

    def add_leader(self, external_id, label=None, allocation_pct=0.1):
        session = get_session()
        try:
            ldr = CopyLeader(
                external_id=external_id,
                label=label or external_id,
                allocation_pct=allocation_pct,
                is_active=True,
            )
            session.add(ldr)
            session.commit()
            return ldr
        finally:
            session.close()

    def remove_leader(self, external_id):
        session = get_session()
        try:
            ldr = session.query(CopyLeader).filter_by(external_id=external_id).first()
            if ldr:
                ldr.is_active = False
                session.commit()
        finally:
            session.close()


# ═══════════════════════════════════════════════════════
#  Background tasks  — keeps data live while dashboard runs
# ═══════════════════════════════════════════════════════

def background_tasks(exchange, portfolio_tracker, risk_manager, strategies,
                     is_paper=True):
    """Run periodic updates in a background thread."""
    logger.info("Background tasks started")

    cycle = 0
    while True:
        try:
            # Update open position prices every 10s
            session = get_session()
            try:
                positions = session.query(Position).filter_by(is_open=True).all()
                for p in positions:
                    try:
                        price = exchange.get_price(p.symbol)
                        p.current_price = price
                        if p.side == "long":
                            p.unrealized_pnl = (price - p.entry_price) * p.amount
                        else:
                            p.unrealized_pnl = (p.entry_price - price) * p.amount
                    except Exception:
                        pass
                session.commit()
            except Exception as e:
                session.rollback()
                logger.debug("Position update error: %s", e)
            finally:
                session.close()

            # Portfolio snapshot every ~5 minutes (30 cycles)
            if cycle % 30 == 0 and cycle > 0:
                try:
                    portfolio_tracker.take_snapshot()
                except Exception as e:
                    logger.debug("Snapshot error: %s", e)

            # Update peak balance every ~2 minutes
            if cycle % 12 == 0:
                try:
                    bal = exchange.get_balance()
                    total = bal.get("USDT", {}).get("total", 0)
                    risk_manager.update_peak_balance(total)
                except Exception:
                    pass

            # Simulate a random AI signal every ~3 minutes (paper only)
            if is_paper and cycle % 18 == 0 and cycle > 0:
                try:
                    session = get_session()
                    sym = random.choice(SYMBOLS)
                    action = random.choices(
                        ["buy", "sell", "hold"], weights=[0.35, 0.30, 0.35]
                    )[0]
                    sig = Signal(
                        source="ai", symbol=sym, timeframe="1h",
                        action=action,
                        confidence=random.uniform(0.4, 0.95),
                        ta_score=random.uniform(-1, 1),
                        ml_score=random.uniform(-1, 1),
                        acted_on=False,
                    )
                    session.add(sig)
                    session.commit()
                    session.close()
                except Exception:
                    pass

        except Exception as e:
            logger.error("Background task error: %s", e)

        cycle += 1
        time.sleep(10)


# ═══════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════

def _load_env_config():
    """Load configuration from .env file."""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv is optional, user can export env vars directly


def _create_live_exchange(testnet: bool):
    """Create a live Binance exchange client. Exits on failure."""
    api_key = os.environ.get("BINANCE_API_KEY", "")
    api_secret = os.environ.get("BINANCE_API_SECRET", "")

    if not api_key or api_key == "your_api_key_here":
        print("\n  ERROR: BINANCE_API_KEY not configured!")
        print("  Set it in your .env file or export it as an environment variable.")
        print("  See .env.example for details.\n")
        sys.exit(1)
    if not api_secret or api_secret == "your_api_secret_here":
        print("\n  ERROR: BINANCE_API_SECRET not configured!")
        print("  Set it in your .env file or export it as an environment variable.\n")
        sys.exit(1)

    from bot.exchange.client import ExchangeClient
    exchange = ExchangeClient(
        api_key=api_key,
        api_secret=api_secret,
        testnet=testnet,
    )
    if not exchange.connect():
        print("\n  ERROR: Failed to connect to Binance. Check your API keys.\n")
        sys.exit(1)
    return exchange


def main():
    parser = argparse.ArgumentParser(description="Crypto Trading Bot Dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port (default 8080)")
    parser.add_argument("--host", default="0.0.0.0", help="Host (default 0.0.0.0)")
    parser.add_argument(
        "--mode", choices=["paper", "live"], default="paper",
        help="Trading mode: 'paper' (simulated) or 'live' (real money)",
    )
    parser.add_argument(
        "--testnet", action="store_true",
        help="Use Binance testnet instead of production (live mode only)",
    )
    parser.add_argument(
        "--confirm-live", action="store_true",
        help="Skip the interactive confirmation prompt for live mode",
    )
    args = parser.parse_args()

    is_paper = args.mode == "paper"

    # Set env so any imported settings module sees the right mode
    os.environ["TRADING_MODE"] = args.mode

    # ── Live mode safety checks ──────────────────────
    if not is_paper:
        _load_env_config()

        if not args.confirm_live:
            print()
            print("  ╔══════════════════════════════════════════════════════╗")
            print("  ║  WARNING: You are about to start in LIVE mode!      ║")
            print("  ║                                                      ║")
            print("  ║  This will connect to Binance with your API keys     ║")
            print("  ║  and trade with REAL MONEY.                          ║")
            print("  ║                                                      ║")
            print("  ║  Make sure you understand the risks before           ║")
            print("  ║  proceeding. All trades are irreversible.            ║")
            print("  ╚══════════════════════════════════════════════════════╝")
            print()
            try:
                answer = input("  Type 'YES' to confirm live trading: ")
            except (EOFError, KeyboardInterrupt):
                print("\n  Aborted.")
                sys.exit(0)
            if answer.strip() != "YES":
                print("  Aborted. Run with --mode paper for simulated trading.")
                sys.exit(0)

    # ── Database setup ───────────────────────────────
    if is_paper:
        db_name = "dashboard.db"
    else:
        db_name = "dashboard_live.db"

    db_path = os.path.join(os.path.dirname(__file__), db_name)
    db_url = f"sqlite:///{db_path}"

    # Paper mode: fresh DB each launch for clean state
    # Live mode: persist DB across restarts to keep trade history
    if is_paper and os.path.exists(db_path):
        os.remove(db_path)

    # ── Boot sequence ────────────────────────────────
    if is_paper:
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║   Crypto Trading Bot  —  Dashboard       ║")
        print("  ║   Mode: PAPER  |  Offline Simulation     ║")
        print("  ╚══════════════════════════════════════════╝")
        print()
    else:
        net_label = "TESTNET" if args.testnet else "PRODUCTION"
        print()
        print("  ╔══════════════════════════════════════════╗")
        print("  ║   Crypto Trading Bot  —  Dashboard       ║")
        print(f"  ║   Mode: LIVE   |  Binance {net_label:<14s}║")
        print("  ╚══════════════════════════════════════════╝")
        print()

    init_db(db_url)

    # ── Exchange setup ───────────────────────────────
    if is_paper:
        exchange = LocalPaperExchange(initial_balance_usdt=10000.0)
        exchange.connect()
        seed_database(exchange)
        initial_balance = 10000.0
    else:
        exchange = _create_live_exchange(testnet=args.testnet)
        balance = exchange.get_balance()
        initial_balance = balance.get("USDT", {}).get("total", 0)
        print(f"  Connected to Binance {'(testnet)' if args.testnet else ''}")
        print(f"  Account balance: ${initial_balance:,.2f} USDT")
        print()

    # ── Managers ─────────────────────────────────────
    risk_manager = RiskManager(
        max_position_size_pct=10.0,
        max_positions=5,
        daily_loss_limit_pct=5.0,
        stop_loss_pct=3.0,
        take_profit_pct=6.0,
        trailing_stop_pct=2.0,
        max_drawdown_pct=15.0,
        cooldown_after_losses=3,
        cooldown_minutes=60,
    )
    risk_manager.update_peak_balance(initial_balance)

    order_manager = OrderManager(
        exchange_client=exchange,
        risk_manager=risk_manager,
        is_paper=is_paper,
    )

    portfolio_tracker = PortfolioTracker(
        exchange_client=exchange,
        is_paper=is_paper,
    )

    # Strategy wrappers
    ai_trader = DashboardStrategy("ai", active=True)
    copy_trader = DashboardStrategy("copy", active=True)
    signal_follower = DashboardStrategy("signal", active=False)

    # Take initial snapshot
    portfolio_tracker.take_snapshot()

    # ── Dashboard app ────────────────────────────────
    app = create_dashboard(
        portfolio_tracker=portfolio_tracker,
        order_manager=order_manager,
        risk_manager=risk_manager,
        copy_trader=copy_trader,
        signal_follower=signal_follower,
        ai_trader=ai_trader,
    )

    # ── Background thread ────────────────────────────
    bg = threading.Thread(
        target=background_tasks,
        args=(exchange, portfolio_tracker, risk_manager,
              [ai_trader, copy_trader, signal_follower]),
        kwargs={"is_paper": is_paper},
        daemon=True,
    )
    bg.start()

    # ── Serve ────────────────────────────────────────
    url = f"http://localhost:{args.port}"
    mode_label = "PAPER" if is_paper else "LIVE"
    print(f"  Dashboard:  {url}")
    print(f"  API docs:   {url}/docs")
    print(f"  Mode:       {mode_label}")
    print()
    print("  Press Ctrl+C to stop.")
    print()

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
