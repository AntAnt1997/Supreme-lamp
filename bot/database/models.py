"""SQLAlchemy ORM models for the trading bot database."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(4), nullable=False)  # "buy" or "sell"
    order_type = Column(String(10), nullable=False, default="market")  # "market" or "limit"
    amount = Column(Float, nullable=False)
    price = Column(Float, nullable=True)  # Limit price (None for market)
    average_price = Column(Float, nullable=True)  # Actual fill price
    cost = Column(Float, nullable=True)  # Total cost (amount * avg_price)
    fee = Column(Float, default=0.0)
    fee_currency = Column(String(10), nullable=True)
    strategy = Column(String(20), nullable=False, index=True)  # "copy", "signal", "ai", "manual"
    order_id = Column(String(255), nullable=True)  # Exchange order ID
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending/filled/canceled/failed
    pnl = Column(Float, nullable=True)  # Realized PnL (set on close)
    is_paper = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime, nullable=True)

    # Foreign keys for traceability
    leader_id = Column(String(255), nullable=True)  # Copy trading: which leader
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)

    __table_args__ = (
        Index("ix_trades_symbol_status", "symbol", "status"),
    )

    def __repr__(self):
        return f"<Trade {self.side} {self.amount} {self.symbol} @ {self.average_price}>"


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(5), nullable=False)  # "long" or "short"
    entry_price = Column(Float, nullable=False)
    amount = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float, default=0.0)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    strategy = Column(String(20), nullable=False)
    is_paper = Column(Boolean, default=True)
    is_open = Column(Boolean, default=True, index=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_positions_open", "is_open", "symbol"),
    )

    def __repr__(self):
        return f"<Position {self.side} {self.amount} {self.symbol} @ {self.entry_price}>"


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(20), nullable=False, index=True)  # "ai", "copy", "telegram"
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(5), nullable=True)  # "1h", "4h", "1d"
    action = Column(String(4), nullable=False)  # "buy", "sell", "hold"
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    ta_score = Column(Float, nullable=True)  # Technical analysis sub-score
    ml_score = Column(Float, nullable=True)  # ML model sub-score
    metadata_json = Column(Text, nullable=True)  # Extra signal data as JSON
    acted_on = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship to trades
    trades = relationship("Trade", backref="signal", foreign_keys=[Trade.signal_id])

    def __repr__(self):
        return f"<Signal {self.action} {self.symbol} confidence={self.confidence:.2f}>"


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    total_balance = Column(Float, nullable=False)  # Total portfolio value in USDT
    available_balance = Column(Float, nullable=False)  # Free balance
    in_positions = Column(Float, nullable=False, default=0.0)  # Balance in open positions
    total_pnl = Column(Float, default=0.0)  # All-time realized PnL
    daily_pnl = Column(Float, default=0.0)  # Today's PnL
    unrealized_pnl = Column(Float, default=0.0)  # Current unrealized PnL
    num_open_positions = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Snapshot balance={self.total_balance:.2f} pnl={self.daily_pnl:.2f}>"


class CopyLeader(Base):
    __tablename__ = "copy_leaders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String(255), nullable=False, unique=True)  # Trader ID on exchange
    label = Column(String(100), nullable=True)  # Human-readable label
    allocation_pct = Column(Float, default=0.1)  # % of our capital to mirror (0.0-1.0)
    is_active = Column(Boolean, default=True)
    last_polled_at = Column(DateTime, nullable=True)
    total_pnl = Column(Float, default=0.0)  # PnL from copying this leader
    num_trades_copied = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CopyLeader {self.label or self.external_id}>"


class Withdrawal(Base):
    __tablename__ = "withdrawals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    currency = Column(String(10), nullable=False)
    amount = Column(Float, nullable=False)
    destination = Column(String(255), nullable=False)  # Bank IBAN or crypto address
    method = Column(String(50), nullable=True)  # "bank_wire", "sepa", "ach", "crypto"
    exchange_txn_id = Column(String(255), nullable=True)
    status = Column(String(20), default="pending")  # pending/processing/completed/failed
    fee = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Withdrawal {self.amount} {self.currency} -> {self.destination[:20]}>"


class AppSetting(Base):
    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AppSetting {self.key}={self.value[:50]}>"


# ── Wallet Tracking Models ────────────────────────────────────────────────────


class TrackedWallet(Base):
    """An externally-tracked blockchain wallet address."""

    __tablename__ = "tracked_wallets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String(255), nullable=False, unique=True, index=True)
    label = Column(String(100), nullable=True)
    chain = Column(String(20), nullable=False, default="ethereum")  # ethereum/polygon/arbitrum/base/optimism/bsc
    # Optional Polymarket metadata
    polymarket_volume = Column(Float, nullable=True)
    polymarket_win_rate = Column(Float, nullable=True)
    polymarket_pnl = Column(Float, nullable=True)
    # Sync metadata
    last_synced_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tokens = relationship("WalletToken", back_populates="wallet", cascade="all, delete-orphan")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")
    snapshots = relationship("WalletSnapshot", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TrackedWallet {self.label or self.address[:10]}...>"


class WalletToken(Base):
    """Current token holdings for a tracked wallet."""

    __tablename__ = "wallet_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(Integer, ForeignKey("tracked_wallets.id", ondelete="CASCADE"), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    token_name = Column(String(100), nullable=True)
    token_address = Column(String(255), nullable=True)  # contract address (None for native)
    balance = Column(Float, nullable=False, default=0.0)
    balance_usd = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    wallet = relationship("TrackedWallet", back_populates="tokens")

    __table_args__ = (
        Index("ix_wallet_tokens_wallet_symbol", "wallet_id", "token_symbol"),
    )

    def __repr__(self):
        return f"<WalletToken {self.token_symbol} bal={self.balance}>"


class WalletTransaction(Base):
    """Transaction history for a tracked wallet."""

    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(Integer, ForeignKey("tracked_wallets.id", ondelete="CASCADE"), nullable=False)
    tx_hash = Column(String(255), nullable=False, index=True)
    block_number = Column(Integer, nullable=True)
    tx_type = Column(String(20), nullable=True)  # "send", "receive", "swap", "contract"
    from_address = Column(String(255), nullable=True)
    to_address = Column(String(255), nullable=True)
    asset = Column(String(20), nullable=True)
    value = Column(Float, nullable=True)
    value_usd = Column(Float, nullable=True)
    gas_used = Column(Float, nullable=True)
    gas_price_gwei = Column(Float, nullable=True)
    fee_usd = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)  # "success" / "failed"
    timestamp = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    wallet = relationship("TrackedWallet", back_populates="transactions")

    __table_args__ = (
        Index("ix_wallet_tx_wallet_ts", "wallet_id", "timestamp"),
    )

    def __repr__(self):
        return f"<WalletTransaction {self.tx_hash[:10]}... {self.asset}>"


class WalletSnapshot(Base):
    """Periodic total-value snapshot for portfolio history."""

    __tablename__ = "wallet_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wallet_id = Column(Integer, ForeignKey("tracked_wallets.id", ondelete="CASCADE"), nullable=False)
    total_value_usd = Column(Float, nullable=False, default=0.0)
    native_balance = Column(Float, nullable=True)
    native_balance_usd = Column(Float, nullable=True)
    token_count = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    wallet = relationship("TrackedWallet", back_populates="snapshots")

    def __repr__(self):
        return f"<WalletSnapshot wallet={self.wallet_id} usd={self.total_value_usd:.2f}>"
