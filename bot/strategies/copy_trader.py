"""Copy trading strategy - monitors and replicates trades from top traders."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from bot.strategies.base import BaseStrategy
from bot.database.db import get_session
from bot.database.models import CopyLeader, Trade

logger = logging.getLogger(__name__)


class CopyTrader(BaseStrategy):
    """
    Monitors top traders and replicates their trades proportionally.

    Copy Trading Workflow:
    1. Poll each active leader's recent trades via exchange API
    2. Detect new trades not yet replicated
    3. Calculate proportional position size based on allocation_pct
    4. Queue or execute trades based on auto_approve flag
    5. Track all copied trades with leader reference
    """

    def __init__(
        self,
        order_manager,
        exchange_client,
        risk_manager=None,
        notifier=None,
        trade_ratio: float = 0.1,
        min_trade_usdt: float = 10.0,
        max_trade_usdt: float = 5000.0,
        auto_approve: bool = False,
    ):
        super().__init__("copy", order_manager, risk_manager, notifier)
        self.exchange = exchange_client
        self.trade_ratio = trade_ratio
        self.min_trade_usdt = min_trade_usdt
        self.max_trade_usdt = max_trade_usdt
        self.auto_approve = auto_approve

        # Cache of seen trade IDs per leader to avoid duplicates
        self._seen_trades: dict[str, set] = {}

        # Pending trades awaiting manual approval (when auto_approve=False)
        # Each entry: {id, leader_id, label, symbol, side, amount, price, value, detected_at}
        self._pending_trades: list[dict] = []

    def run(self) -> list:
        """Execute one copy trading cycle - check all leaders for new trades."""
        if not self.is_active:
            return []

        orders = []
        session = get_session()
        try:
            leaders = session.query(CopyLeader).filter_by(is_active=True).all()
            if not leaders:
                return []

            for leader in leaders:
                try:
                    new_orders = self._process_leader(leader, session)
                    orders.extend(new_orders)
                except Exception as e:
                    logger.error(
                        "Error processing leader %s: %s", leader.external_id, e
                    )

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Copy trading cycle error: %s", e)
        finally:
            session.close()

        return orders

    def get_config(self) -> dict:
        """Return current copy trading configuration."""
        return {
            "trade_ratio": self.trade_ratio,
            "min_trade_usdt": self.min_trade_usdt,
            "max_trade_usdt": self.max_trade_usdt,
            "auto_approve": self.auto_approve,
        }

    def update_config(
        self,
        trade_ratio: Optional[float] = None,
        min_trade_usdt: Optional[float] = None,
        max_trade_usdt: Optional[float] = None,
        auto_approve: Optional[bool] = None,
    ) -> dict:
        """Update copy trading configuration at runtime."""
        if trade_ratio is not None:
            self.trade_ratio = max(0.01, min(1.0, trade_ratio))
        if min_trade_usdt is not None:
            self.min_trade_usdt = max(0.0, min_trade_usdt)
        if max_trade_usdt is not None:
            self.max_trade_usdt = max(0.0, max_trade_usdt)
        if auto_approve is not None:
            self.auto_approve = auto_approve
        logger.info(
            "Copy trading config updated: ratio=%.2f min=$%.0f max=$%.0f auto=%s",
            self.trade_ratio, self.min_trade_usdt, self.max_trade_usdt, self.auto_approve,
        )
        return self.get_config()

    def get_pending_trades(self) -> list[dict]:
        """Return trades awaiting manual approval."""
        return list(self._pending_trades)

    def approve_trade(self, pending_id: str) -> Optional[dict]:
        """Approve and execute a pending copy trade."""
        entry = self._pop_pending(pending_id)
        if not entry:
            return None
        order = self._place_order(
            symbol=entry["symbol"],
            side=entry["side"],
            amount=entry["amount"],
            leader_id=entry["leader_id"],
        )
        if order and self.notifier:
            self.notifier.send(
                f"✅ COPY TRADE EXECUTED\n"
                f"{entry['side'].upper()} {entry['amount']:.6f} {entry['symbol']}\n"
                f"Leader: {entry['label']}"
            )
        return order

    def reject_trade(self, pending_id: str) -> bool:
        """Reject and discard a pending copy trade."""
        entry = self._pop_pending(pending_id)
        if entry:
            logger.info("Rejected pending copy trade %s (%s %s)", pending_id, entry["side"], entry["symbol"])
            return True
        return False

    def _pop_pending(self, pending_id: str) -> Optional[dict]:
        for i, entry in enumerate(self._pending_trades):
            if entry["id"] == pending_id:
                return self._pending_trades.pop(i)
        return None

    def get_copy_stats(self, days: int = 7) -> dict:
        """Return copy trading statistics for the last N days."""
        session = get_session()
        try:
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
            trades = (
                session.query(Trade)
                .filter(Trade.strategy == "copy", Trade.created_at >= cutoff)
                .all()
            )
            num_trades = len(trades)
            closed = [t for t in trades if t.pnl is not None]
            wins = [t for t in closed if t.pnl > 0]
            total_pnl = sum(t.pnl for t in closed)
            total_volume = sum((t.cost or 0) for t in trades)
            win_rate = (len(wins) / len(closed) * 100) if closed else 0.0
            return {
                "period_days": days,
                "num_trades": num_trades,
                "closed_trades": len(closed),
                "wins": len(wins),
                "win_rate_pct": round(win_rate, 1),
                "total_pnl": round(total_pnl, 2),
                "total_volume_usdt": round(total_volume, 2),
            }
        finally:
            session.close()

    def get_copy_history(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """Return recent copy trades."""
        session = get_session()
        try:
            trades = (
                session.query(Trade)
                .filter_by(strategy="copy")
                .order_by(Trade.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "amount": t.amount,
                    "price": t.average_price,
                    "cost": t.cost,
                    "pnl": t.pnl,
                    "status": t.status,
                    "leader_id": t.leader_id,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "closed_at": t.closed_at.isoformat() if t.closed_at else None,
                }
                for t in trades
            ]
        finally:
            session.close()

    def add_leader(
        self,
        external_id: str,
        label: Optional[str] = None,
        allocation_pct: float = 0.1,
    ) -> CopyLeader:
        """Add a new leader to track."""
        session = get_session()
        try:
            leader = CopyLeader(
                external_id=external_id,
                label=label or external_id,
                allocation_pct=allocation_pct,
                is_active=True,
            )
            session.add(leader)
            session.commit()
            logger.info("Added copy leader: %s (allocation: %.1f%%)", label, allocation_pct * 100)
            return leader
        except Exception as e:
            session.rollback()
            logger.error("Failed to add leader: %s", e)
            raise
        finally:
            session.close()

    def remove_leader(self, external_id: str):
        """Deactivate a leader."""
        session = get_session()
        try:
            leader = session.query(CopyLeader).filter_by(external_id=external_id).first()
            if leader:
                leader.is_active = False
                session.commit()
                logger.info("Deactivated leader: %s", external_id)
        finally:
            session.close()

    def get_leaders(self) -> list:
        """Get all copy trading leaders."""
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

    def get_status(self) -> dict:
        """Get copy trading strategy status."""
        session = get_session()
        try:
            active_leaders = session.query(CopyLeader).filter_by(is_active=True).count()
            total_copied = (
                session.query(Trade).filter_by(strategy="copy").count()
            )
            total_pnl = sum(
                t.pnl or 0
                for t in session.query(Trade)
                .filter_by(strategy="copy")
                .filter(Trade.pnl.isnot(None))
                .all()
            )
            return {
                "strategy": "copy",
                "is_active": self.is_active,
                "active_leaders": active_leaders,
                "total_trades_copied": total_copied,
                "total_pnl": total_pnl,
                "trade_ratio": self.trade_ratio,
            }
        finally:
            session.close()

    def _process_leader(self, leader: CopyLeader, session) -> list:
        """Check a single leader for new trades and replicate them."""
        orders = []

        # Initialize seen trades set for this leader
        if leader.external_id not in self._seen_trades:
            self._seen_trades[leader.external_id] = set()
            # On first run, load existing copied trades to avoid duplicates
            existing = (
                session.query(Trade)
                .filter_by(strategy="copy", leader_id=leader.external_id)
                .all()
            )
            for t in existing:
                if t.order_id:
                    self._seen_trades[leader.external_id].add(t.order_id)

        # Fetch leader's recent trades
        since = None
        if leader.last_polled_at:
            since = int(leader.last_polled_at.timestamp() * 1000)

        try:
            # This requires the leader's API key to be configured
            # In practice, you'd have a separate exchange client for each leader
            leader_trades = self.exchange.get_my_trades(since=since, limit=50)
        except Exception as e:
            logger.error("Failed to fetch trades for leader %s: %s", leader.external_id, e)
            return orders

        # Filter to new trades only
        for trade in leader_trades:
            trade_id = trade.get("id", "")
            if trade_id in self._seen_trades[leader.external_id]:
                continue

            self._seen_trades[leader.external_id].add(trade_id)

            # Calculate our position size
            our_amount = self._calculate_copy_amount(trade, leader)
            if our_amount <= 0:
                continue

            symbol = trade.get("symbol", "")
            side = trade.get("side", "")
            price = trade.get("price", 0)
            trade_value = our_amount * price

            # Verify minimum trade size
            if trade_value < self.min_trade_usdt:
                logger.debug(
                    "Skipping copy trade: value %.2f < min %.2f",
                    trade_value, self.min_trade_usdt,
                )
                continue

            # Cap at maximum trade size
            if self.max_trade_usdt > 0 and trade_value > self.max_trade_usdt:
                our_amount = self.max_trade_usdt / price if price > 0 else our_amount
                trade_value = our_amount * price
                logger.debug(
                    "Capping copy trade to max $%.0f: %.6f %s",
                    self.max_trade_usdt, our_amount, symbol,
                )

            if self.auto_approve:
                # Execute immediately
                order = self._place_order(
                    symbol=symbol,
                    side=side,
                    amount=our_amount,
                    leader_id=leader.external_id,
                )
                if order:
                    orders.append(order)
                    leader.num_trades_copied += 1

                    if self.notifier:
                        self.notifier.send(
                            f"✅ COPY TRADE EXECUTED\n"
                            f"Leader: {leader.label}\n"
                            f"{side.upper()} {our_amount:.6f} {symbol}\n"
                            f"Value: ${trade_value:,.2f}"
                        )
            else:
                # Queue for manual approval
                pending = {
                    "id": str(uuid.uuid4()),
                    "leader_id": leader.external_id,
                    "label": leader.label,
                    "symbol": symbol,
                    "side": side,
                    "amount": our_amount,
                    "price": price,
                    "value": trade_value,
                    "detected_at": datetime.utcnow().isoformat(),
                }
                self._pending_trades.append(pending)
                logger.info(
                    "Pending approval: %s %s %.6f %s ($%.2f)",
                    side.upper(), our_amount, symbol, trade_value, trade_value,
                )

                if self.notifier:
                    self.notifier.send(
                        f"📋 COPY TRADE DETECTED\n\n"
                        f"Original Trader: {leader.label}\n"
                        f"Trade: {side.upper()} {symbol}\n"
                        f"Value: ${trade_value:,.2f}\n\n"
                        f"⏳ Awaiting approval"
                    )

        leader.last_polled_at = datetime.utcnow()
        return orders

    def _calculate_copy_amount(self, leader_trade: dict, leader: CopyLeader) -> float:
        """Calculate our position size proportional to the leader's trade."""
        leader_amount = leader_trade.get("amount", 0)
        leader_price = leader_trade.get("price", 0)

        if leader_amount <= 0 or leader_price <= 0:
            return 0

        # Get our available balance
        balance = self.exchange.get_balance()
        available_usdt = balance.get("USDT", {}).get("free", 0)

        # Calculate based on allocation percentage
        allocated_usdt = available_usdt * leader.allocation_pct
        our_amount = allocated_usdt / leader_price

        # Apply trade ratio cap
        max_from_ratio = leader_amount * self.trade_ratio
        our_amount = min(our_amount, max_from_ratio)

        return our_amount
