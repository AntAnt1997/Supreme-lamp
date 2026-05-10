"""Tests for the wallet tracking module."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from bot.database.models import Base, TrackedWallet, WalletToken, WalletSnapshot, WalletTransaction
from bot.wallet.service import WalletService, _wallet_to_dict
from bot.wallet.blockchain import BlockchainService


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def wallet_db(monkeypatch):
    """In-memory SQLite database with wallet tables."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    import bot.database.db as db_module
    monkeypatch.setattr(db_module, "_engine", engine)
    monkeypatch.setattr(db_module, "_SessionFactory", Session)

    yield session
    session.close()


@pytest.fixture
def svc(wallet_db):
    """WalletService with a mock blockchain backend."""
    mock_blockchain = MagicMock(spec=BlockchainService)
    mock_blockchain.sync_wallet.return_value = {
        "address": "0xabc123",
        "chain": "ethereum",
        "native": {
            "symbol": "ETH",
            "name": "Ethereum",
            "balance": 1.5,
            "price_usd": 3000.0,
            "balance_usd": 4500.0,
            "token_address": None,
        },
        "tokens": [
            {
                "symbol": "USDC",
                "name": "USD Coin",
                "balance": 1000.0,
                "price_usd": 1.0,
                "balance_usd": 1000.0,
                "token_address": "0xusdc",
            }
        ],
        "transactions": [
            {
                "tx_hash": "0xdeadbeef",
                "block_number": 12345,
                "tx_type": "receive",
                "from_address": "0xsender",
                "to_address": "0xabc123",
                "asset": "ETH",
                "value": 1.5,
                "value_usd": 4500.0,
                "gas_used": None,
                "gas_price_gwei": None,
                "fee_usd": None,
                "status": "success",
                "timestamp": datetime(2024, 1, 1),
            }
        ],
        "total_value_usd": 5500.0,
        "synced_at": datetime(2024, 1, 1, 12, 0),
    }
    return WalletService(blockchain=mock_blockchain)


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestWalletCRUD:
    def test_add_wallet(self, svc, wallet_db):
        w = svc.add_wallet("0xABC123", chain="ethereum", label="Test")
        assert w["address"] == "0xabc123"  # lowercased
        assert w["chain"] == "ethereum"
        assert w["label"] == "Test"
        assert w["id"] is not None

    def test_add_duplicate_wallet_raises(self, svc, wallet_db):
        svc.add_wallet("0xABC123", chain="ethereum")
        with pytest.raises(ValueError, match="already tracked"):
            svc.add_wallet("0xabc123", chain="polygon")

    def test_list_wallets(self, svc, wallet_db):
        svc.add_wallet("0x111", chain="ethereum", label="A")
        svc.add_wallet("0x222", chain="polygon", label="B")
        wallets = svc.list_wallets()
        assert len(wallets) == 2
        labels = {w["label"] for w in wallets}
        assert labels == {"A", "B"}

    def test_get_wallet(self, svc, wallet_db):
        added = svc.add_wallet("0xfeed", chain="arbitrum", label="Feed")
        fetched = svc.get_wallet(added["id"])
        assert fetched is not None
        assert fetched["label"] == "Feed"

    def test_get_wallet_missing(self, svc, wallet_db):
        assert svc.get_wallet(9999) is None

    def test_update_wallet(self, svc, wallet_db):
        added = svc.add_wallet("0xbeef", chain="base")
        updated = svc.update_wallet(added["id"], label="Updated Label")
        assert updated["label"] == "Updated Label"

    def test_delete_wallet(self, svc, wallet_db):
        added = svc.add_wallet("0xcafe", chain="optimism")
        svc.delete_wallet(added["id"])
        assert svc.get_wallet(added["id"]) is None

    def test_delete_wallet_missing(self, svc, wallet_db):
        with pytest.raises(ValueError):
            svc.delete_wallet(9999)


class TestWalletSync:
    def test_sync_persists_tokens(self, svc, wallet_db):
        added = svc.add_wallet("0xabc123", chain="ethereum")
        result = svc.sync_wallet(added["id"])
        assert result["total_value_usd"] == 5500.0
        tokens = svc.get_wallet_tokens(added["id"])
        symbols = {t["token_symbol"] for t in tokens}
        assert "ETH" in symbols
        assert "USDC" in symbols

    def test_sync_persists_transactions(self, svc, wallet_db):
        added = svc.add_wallet("0xabc123", chain="ethereum")
        svc.sync_wallet(added["id"])
        txns = svc.get_wallet_transactions(added["id"])
        assert len(txns) == 1
        assert txns[0]["tx_hash"] == "0xdeadbeef"

    def test_sync_no_duplicate_transactions(self, svc, wallet_db):
        added = svc.add_wallet("0xabc123", chain="ethereum")
        svc.sync_wallet(added["id"])
        svc.sync_wallet(added["id"])  # second sync
        txns = svc.get_wallet_transactions(added["id"])
        assert len(txns) == 1  # no duplicates

    def test_sync_wallet_not_found(self, svc, wallet_db):
        with pytest.raises(ValueError):
            svc.sync_wallet(9999)


class TestPortfolioSummary:
    def test_empty_summary(self, svc, wallet_db):
        summary = svc.get_portfolio_summary()
        assert summary["total_wallets"] == 0
        assert summary["total_value_usd"] == 0.0

    def test_summary_counts_wallets(self, svc, wallet_db):
        svc.add_wallet("0x111", chain="ethereum")
        svc.add_wallet("0x222", chain="polygon")
        summary = svc.get_portfolio_summary()
        assert summary["total_wallets"] == 2


class TestPolymarketImport:
    def test_import_wallets(self, svc, wallet_db):
        data = [
            {"address": "0xAAA", "label": "Trader 1", "performance": {"total_volume": 100000, "win_rate": 70.0, "profit_loss": 5000}},
            {"address": "0xBBB", "label": "Trader 2"},
        ]
        result = svc.import_polymarket_wallets(data)
        assert result["added"] == 2
        assert result["skipped"] == 0
        wallets = svc.list_wallets()
        assert len(wallets) == 2

    def test_import_skips_duplicates(self, svc, wallet_db):
        svc.add_wallet("0xaaa")
        data = [{"address": "0xAAA", "label": "Dup"}]
        result = svc.import_polymarket_wallets(data)
        assert result["added"] == 0
        assert result["skipped"] == 1

    def test_import_handles_missing_address(self, svc, wallet_db):
        data = [{"label": "No address"}]
        result = svc.import_polymarket_wallets(data)
        assert result["added"] == 0
        assert len(result["errors"]) == 1
