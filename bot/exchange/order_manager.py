"""Order manager - routes orders through exchange client or paper trader with risk checks."""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from bot.database.db import get_session
from bot.database.models import Trade, Position

logger = logging.getLogger(__name__)


class OrderManager:
    """
    Central order routing and management.
    Routes orders through either the live exchange or paper trader.
    Records all trades in the database and manages positions.
    """

    def __init__(self, exchange_client, risk_manager=None, notifier=None, is_paper: bool = True):
        self.client = exchange_client
        self.risk_manager = risk_manager
        self.notifier = notifier
        self.is_paper = is_paper

    def place_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        strategy: str = "manual",
        signal_id: Optional[int] = None,
        leader_id: Optional[str] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Optional[dict]:
        """
        Place an order with risk checks, execute via exchange, and record in DB.

        Returns the order result dict or None if rejected by risk manager.
        """
        # Run risk check if risk manager is available
        if self.risk_manager:
            current_price = price or self.client.get_price(symbol)
            risk_decision = self.risk_manager.pre_trade_check(
                symbol=symbol,
                side=side,
                amount=amount,
                price=current_price,
            )
            if not risk_decision["allowed"]:
                logger.warning(
                    "Order rejected by risk manager: %s", risk_decision["reason"]
                )
                if self.notifier:
                    self.notifier.send(
                        f"⚠️ Order REJECTED: {side} {amount} {symbol}\n"
                        f"Reason: {risk_decision['reason']}"
                    )
                return None

            # Use adjusted amount if risk manager modified it
            amount = risk_decision.get("adjusted_amount", amount)
            stop_loss = stop_loss or risk_decision.get("stop_loss")
            take_profit = take_profit or risk_decision.get("take_profit")

        # Execute the order
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                amount=amount,
                price=price,
            )
        except Exception as e:
            logger.error("Order execution failed: %s", e)
            if self.notifier:
                self.notifier.send(f"❌ Order FAILED: {side} {amount} {symbol}\nError: {e}")
            raise

        # Record trade and update position in a single DB transaction
        session = get_session()
        try:
            self._record_trade(
                session, order, symbol, side, amount, strategy,
                signal_id, leader_id, stop_loss, take_profit,
            )

            if order.get("status") in ("closed", "filled"):
                pnl = self._update_position(
                    session, symbol, side, amount, order, strategy,
                    stop_loss, take_profit,
                )
                # Update the trade's PnL if a position was closed
                if pnl is not None:
                    trade = session.query(Trade).filter_by(
                        order_id=order.get("id"), is_paper=self.is_paper,
                    ).order_by(Trade.id.desc()).first()
                    if trade:
                        trade.pnl = pnl

            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Failed to record trade/position: %s", e)
        finally:
            session.close()

        # Send notification
        if self.notifier:
            fill_price = order.get("average") or order.get("price", 0)
            cost = order.get("cost", amount * (fill_price or 0))
            mode = "📄 PAPER" if self.is_paper else "💰 LIVE"
            self.notifier.send(
                f"{mode} | {side.upper()} {symbol}\n"
                f"Amount: {amount}\n"
                f"Price: {fill_price}\n"
                f"Cost: {cost:.2f} USDT\n"
                f"Strategy: {strategy}\n"
                f"SL: {stop_loss or 'None'} | TP: {take_profit or 'None'}"
            )

        return order

    def close_position(self, position_id: int) -> Optional[dict]:
        """Close an open position by placing an opposite order."""
        session = get_session()
        try:
            position = session.query(Position).filter_by(
                id=position_id, is_open=True, is_paper=self.is_paper,
            ).first()

            if not position:
                logger.warning("Position %s not found or already closed", position_id)
                return None

            # Place opposite order
            close_side = "sell" if position.side == "long" else "buy"
            order = self.client.create_order(
                symbol=position.symbol,
                side=close_side,
                order_type="market",
                amount=position.amount,
            )

            # Calculate PnL
            fill_price = order.get("average") or order.get("price", 0)
            if position.side == "long":
                pnl = (fill_price - position.entry_price) * position.amount
            else:
                pnl = (position.entry_price - fill_price) * position.amount

            # Update position
            position.is_open = False
            position.closed_at = datetime.utcnow()
            position.realized_pnl = pnl
            position.current_price = fill_price

            # Record the closing trade in the same session/transaction
            self._record_trade(
                session, order, position.symbol, close_side, position.amount,
                position.strategy, pnl=pnl,
            )

            session.commit()

            if self.notifier:
                emoji = "🟢" if pnl >= 0 else "🔴"
                self.notifier.send(
                    f"{emoji} Position CLOSED: {position.symbol}\n"
                    f"Entry: {position.entry_price} → Exit: {fill_price}\n"
                    f"PnL: {pnl:+.2f} USDT"
                )

            logger.info(
                "Closed position %s: %s PnL=%.2f", position_id, position.symbol, pnl
            )
            return order

        except Exception as e:
            session.rollback()
            logger.error("Failed to close position %s: %s", position_id, e)
            raise
        finally:
            session.close()

    def _record_trade(
        self,
        session: Session,
        order: dict,
        symbol: str,
        side: str,
        amount: float,
        strategy: str = "manual",
        signal_id: Optional[int] = None,
        leader_id: Optional[str] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        pnl: Optional[float] = None,
    ):
        """Record a trade in the database using the provided session."""
        fee_info = order.get("fee", {})
        trade = Trade(
            symbol=symbol,
            side=side,
            order_type=order.get("type", "market"),
            amount=amount,
            price=order.get("price"),
            average_price=order.get("average") or order.get("price"),
            cost=order.get("cost"),
            fee=fee_info.get("cost", 0) if isinstance(fee_info, dict) else 0,
            fee_currency=fee_info.get("currency") if isinstance(fee_info, dict) else None,
            strategy=strategy,
            order_id=order.get("id"),
            status=order.get("status", "filled"),
            pnl=pnl,
            is_paper=self.is_paper,
            signal_id=signal_id,
            leader_id=leader_id,
        )
        session.add(trade)
        logger.debug("Trade recorded: %s", trade)

    def _update_position(
        self,
        session: Session,
        symbol: str,
        side: str,
        amount: float,
        order: dict,
        strategy: str,
        stop_loss: Optional[float],
        take_profit: Optional[float],
    ) -> Optional[float]:
        """Update or create a position based on a filled order.

        Returns realized PnL if a position was closed/reduced, else None.
        """
        fill_price = order.get("average") or order.get("price", 0)
        position_side = "long" if side == "buy" else "short"
        realized_pnl = None

        # Check for existing open position scoped to current trading mode
        existing = session.query(Position).filter_by(
            symbol=symbol, is_open=True, is_paper=self.is_paper,
        ).first()

        if existing:
            if (existing.side == "long" and side == "sell") or \
               (existing.side == "short" and side == "buy"):
                # Closing or reducing position
                closed_amount = min(amount, existing.amount)

                # Compute realized PnL for the closed portion
                if existing.side == "long":
                    realized_pnl = (fill_price - existing.entry_price) * closed_amount
                else:
                    realized_pnl = (existing.entry_price - fill_price) * closed_amount

                if amount >= existing.amount:
                    # Full close
                    existing.realized_pnl = realized_pnl
                    existing.is_open = False
                    existing.closed_at = datetime.utcnow()
                    existing.current_price = fill_price

                    # Handle reversal: excess amount opens a new opposite position
                    remainder = amount - existing.amount
                    if remainder > 0:
                        new_position = Position(
                            symbol=symbol,
                            side=position_side,
                            entry_price=fill_price,
                            amount=remainder,
                            current_price=fill_price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            strategy=strategy,
                            is_paper=self.is_paper,
                            is_open=True,
                        )
                        session.add(new_position)
                else:
                    # Partial close
                    existing.amount -= closed_amount
                    existing.current_price = fill_price
            else:
                # Adding to position - compute new average entry
                total_cost = (existing.entry_price * existing.amount) + (fill_price * amount)
                existing.amount += amount
                existing.entry_price = total_cost / existing.amount
        else:
            # New position
            position = Position(
                symbol=symbol,
                side=position_side,
                entry_price=fill_price,
                amount=amount,
                current_price=fill_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy=strategy,
                is_paper=self.is_paper,
                is_open=True,
            )
            session.add(position)

        return realized_pnl
