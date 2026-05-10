"""Wallet tracking service: CRUD operations and sync orchestration."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from bot.database.db import get_session
from bot.database.models import TrackedWallet, WalletToken, WalletTransaction, WalletSnapshot
from bot.wallet.blockchain import BlockchainService

logger = logging.getLogger(__name__)


class WalletService:
    """Business logic for managing and syncing tracked wallets."""

    def __init__(self, blockchain: BlockchainService | None = None) -> None:
        self.blockchain = blockchain or BlockchainService()

    # ── Wallet CRUD ───────────────────────────────────────────────────────────

    def add_wallet(
        self,
        address: str,
        chain: str = "ethereum",
        label: str | None = None,
        polymarket_volume: float | None = None,
        polymarket_win_rate: float | None = None,
        polymarket_pnl: float | None = None,
    ) -> dict[str, Any]:
        """Add a new tracked wallet. Returns the wallet dict."""
        address = address.strip().lower()
        session = get_session()
        try:
            existing = session.query(TrackedWallet).filter_by(address=address).first()
            if existing:
                raise ValueError(f"Wallet {address} is already tracked.")

            wallet = TrackedWallet(
                address=address,
                chain=chain,
                label=label,
                polymarket_volume=polymarket_volume,
                polymarket_win_rate=polymarket_win_rate,
                polymarket_pnl=polymarket_pnl,
            )
            session.add(wallet)
            session.commit()
            session.refresh(wallet)
            return _wallet_to_dict(wallet)
        finally:
            session.close()

    def get_wallet(self, wallet_id: int) -> dict[str, Any] | None:
        session = get_session()
        try:
            wallet = session.get(TrackedWallet, wallet_id)
            return _wallet_to_dict(wallet) if wallet else None
        finally:
            session.close()

    def list_wallets(self) -> list[dict[str, Any]]:
        session = get_session()
        try:
            wallets = session.query(TrackedWallet).filter_by(is_active=True).order_by(TrackedWallet.created_at.desc()).all()
            return [_wallet_to_dict(w) for w in wallets]
        finally:
            session.close()

    def update_wallet(self, wallet_id: int, **kwargs: Any) -> dict[str, Any]:
        allowed = {"label", "chain", "is_active", "polymarket_volume", "polymarket_win_rate", "polymarket_pnl"}
        session = get_session()
        try:
            wallet = session.get(TrackedWallet, wallet_id)
            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found.")
            for key, val in kwargs.items():
                if key in allowed:
                    setattr(wallet, key, val)
            session.commit()
            session.refresh(wallet)
            return _wallet_to_dict(wallet)
        finally:
            session.close()

    def delete_wallet(self, wallet_id: int) -> None:
        session = get_session()
        try:
            wallet = session.get(TrackedWallet, wallet_id)
            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found.")
            session.delete(wallet)
            session.commit()
        finally:
            session.close()

    # ── Sync ─────────────────────────────────────────────────────────────────

    def sync_wallet(self, wallet_id: int) -> dict[str, Any]:
        """Fetch latest blockchain data and persist it for a tracked wallet."""
        session = get_session()
        try:
            wallet = session.get(TrackedWallet, wallet_id)
            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found.")
            address = wallet.address
            chain = wallet.chain
        finally:
            session.close()

        data = self.blockchain.sync_wallet(address, chain)

        session = get_session()
        try:
            wallet = session.get(TrackedWallet, wallet_id)
            if not wallet:
                raise ValueError(f"Wallet {wallet_id} not found.")

            # ── Upsert tokens ──────────────────────────────────────────────
            all_holdings = [data["native"]] + data["tokens"]
            existing_tokens = {t.token_symbol: t for t in wallet.tokens}
            seen_symbols: set[str] = set()

            for holding in all_holdings:
                symbol = holding["symbol"]
                seen_symbols.add(symbol)
                if symbol in existing_tokens:
                    tok = existing_tokens[symbol]
                else:
                    tok = WalletToken(wallet_id=wallet_id, token_symbol=symbol)
                    session.add(tok)
                tok.token_name = holding.get("name")
                tok.token_address = holding.get("token_address")
                tok.balance = holding.get("balance", 0.0)
                tok.balance_usd = holding.get("balance_usd", 0.0)
                tok.price_usd = holding.get("price_usd", 0.0)

            # Remove stale tokens no longer held
            for symbol, tok in existing_tokens.items():
                if symbol not in seen_symbols:
                    session.delete(tok)

            # ── Persist new transactions ───────────────────────────────────
            existing_hashes = {t.tx_hash for t in wallet.transactions}
            tx_cols = {c.name for c in WalletTransaction.__table__.columns}
            for tx in data["transactions"]:
                if tx["tx_hash"] not in existing_hashes:
                    new_tx = WalletTransaction(
                        wallet_id=wallet_id,
                        **{k: v for k, v in tx.items() if k in tx_cols},
                    )
                    session.add(new_tx)

            # ── Snapshot ───────────────────────────────────────────────────
            native = data["native"]
            snap = WalletSnapshot(
                wallet_id=wallet_id,
                total_value_usd=data["total_value_usd"],
                native_balance=native.get("balance", 0.0),
                native_balance_usd=native.get("balance_usd", 0.0),
                token_count=len(data["tokens"]),
            )
            session.add(snap)

            # ── Update wallet metadata ─────────────────────────────────────
            wallet.last_synced_at = datetime.now(timezone.utc).replace(tzinfo=None)
            session.commit()
        finally:
            session.close()

        return {
            "wallet_id": wallet_id,
            "total_value_usd": data["total_value_usd"],
            "token_count": len(data["tokens"]) + 1,
            "transaction_count": len(data["transactions"]),
            "synced_at": data["synced_at"].isoformat(),
        }

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_wallet_tokens(self, wallet_id: int) -> list[dict[str, Any]]:
        session = get_session()
        try:
            tokens = (
                session.query(WalletToken)
                .filter_by(wallet_id=wallet_id)
                .order_by(WalletToken.balance_usd.desc())
                .all()
            )
            return [_token_to_dict(t) for t in tokens]
        finally:
            session.close()

    def get_wallet_transactions(
        self, wallet_id: int, limit: int = 50, offset: int = 0
    ) -> list[dict[str, Any]]:
        session = get_session()
        try:
            txns = (
                session.query(WalletTransaction)
                .filter_by(wallet_id=wallet_id)
                .order_by(WalletTransaction.timestamp.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            return [_tx_to_dict(t) for t in txns]
        finally:
            session.close()

    def get_portfolio_summary(self) -> dict[str, Any]:
        """Aggregate summary across all tracked wallets."""
        wallets = self.list_wallets()
        total_usd = 0.0
        chain_allocation: dict[str, float] = {}

        session = get_session()
        try:
            for w in wallets:
                tokens = (
                    session.query(WalletToken)
                    .filter_by(wallet_id=w["id"])
                    .all()
                )
                wallet_usd = sum(t.balance_usd or 0.0 for t in tokens)
                total_usd += wallet_usd
                chain = w["chain"]
                chain_allocation[chain] = chain_allocation.get(chain, 0.0) + wallet_usd
        finally:
            session.close()

        return {
            "total_wallets": len(wallets),
            "total_value_usd": total_usd,
            "chain_allocation": chain_allocation,
            "wallets": wallets,
        }

    def get_wallet_history(self, wallet_id: int, days: int = 30) -> list[dict[str, Any]]:
        """Return portfolio value snapshots for the last N days."""
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
        session = get_session()
        try:
            snaps = (
                session.query(WalletSnapshot)
                .filter(WalletSnapshot.wallet_id == wallet_id, WalletSnapshot.timestamp >= cutoff)
                .order_by(WalletSnapshot.timestamp.asc())
                .all()
            )
            return [
                {
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None,
                    "total_value_usd": s.total_value_usd,
                    "native_balance_usd": s.native_balance_usd,
                    "token_count": s.token_count,
                }
                for s in snaps
            ]
        finally:
            session.close()

    # ── Polymarket bulk import ────────────────────────────────────────────────

    def import_polymarket_wallets(self, wallets_data: list[dict[str, Any]]) -> dict[str, Any]:
        """Bulk-import wallets from a Polymarket signal-bot export."""
        added = 0
        skipped = 0
        errors: list[str] = []

        for entry in wallets_data:
            address = entry.get("address", "").strip()
            if not address:
                errors.append("Missing address in entry")
                continue
            perf = entry.get("performance", {})
            try:
                self.add_wallet(
                    address=address,
                    chain=entry.get("chain", "ethereum"),
                    label=entry.get("label"),
                    polymarket_volume=perf.get("total_volume"),
                    polymarket_win_rate=perf.get("win_rate"),
                    polymarket_pnl=perf.get("profit_loss"),
                )
                added += 1
            except ValueError:
                skipped += 1
            except Exception as exc:
                errors.append(f"{address}: {exc}")

        return {"added": added, "skipped": skipped, "errors": errors}


# ── Serialization helpers ─────────────────────────────────────────────────────


def _wallet_to_dict(w: TrackedWallet) -> dict[str, Any]:
    return {
        "id": w.id,
        "address": w.address,
        "label": w.label,
        "chain": w.chain,
        "polymarket_volume": w.polymarket_volume,
        "polymarket_win_rate": w.polymarket_win_rate,
        "polymarket_pnl": w.polymarket_pnl,
        "last_synced_at": w.last_synced_at.isoformat() if w.last_synced_at else None,
        "is_active": w.is_active,
        "created_at": w.created_at.isoformat() if w.created_at else None,
    }


def _token_to_dict(t: WalletToken) -> dict[str, Any]:
    return {
        "id": t.id,
        "wallet_id": t.wallet_id,
        "token_symbol": t.token_symbol,
        "token_name": t.token_name,
        "token_address": t.token_address,
        "balance": t.balance,
        "balance_usd": t.balance_usd,
        "price_usd": t.price_usd,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _tx_to_dict(t: WalletTransaction) -> dict[str, Any]:
    return {
        "id": t.id,
        "wallet_id": t.wallet_id,
        "tx_hash": t.tx_hash,
        "block_number": t.block_number,
        "tx_type": t.tx_type,
        "from_address": t.from_address,
        "to_address": t.to_address,
        "asset": t.asset,
        "value": t.value,
        "value_usd": t.value_usd,
        "gas_used": t.gas_used,
        "fee_usd": t.fee_usd,
        "status": t.status,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
    }
