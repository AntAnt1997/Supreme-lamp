"""Tests for trading strategies."""

from bot.strategies.signal_follower import SignalFollower
from bot.strategies.copy_trader import CopyTrader


class TestCopyTrader:
    """Tests for the CopyTrader strategy."""

    def _make_copy_trader(self, mock_exchange, auto_approve=False):
        from bot.exchange.order_manager import OrderManager

        om = OrderManager.__new__(OrderManager)
        om.client = mock_exchange
        om.risk_manager = None
        om.notifier = None
        om.is_paper = True

        return CopyTrader(
            order_manager=om,
            exchange_client=mock_exchange,
            trade_ratio=0.1,
            min_trade_usdt=10.0,
            max_trade_usdt=5000.0,
            auto_approve=auto_approve,
        )

    def test_initial_config(self, mock_exchange):
        ct = self._make_copy_trader(mock_exchange)
        cfg = ct.get_config()
        assert cfg["trade_ratio"] == 0.1
        assert cfg["min_trade_usdt"] == 10.0
        assert cfg["max_trade_usdt"] == 5000.0
        assert cfg["auto_approve"] is False

    def test_update_config(self, mock_exchange):
        ct = self._make_copy_trader(mock_exchange)
        updated = ct.update_config(trade_ratio=0.2, auto_approve=True)
        assert updated["trade_ratio"] == 0.2
        assert updated["auto_approve"] is True

    def test_update_config_clamps_ratio(self, mock_exchange):
        ct = self._make_copy_trader(mock_exchange)
        ct.update_config(trade_ratio=5.0)  # above 1.0 should clamp to 1.0
        assert ct.trade_ratio == 1.0

        ct.update_config(trade_ratio=-0.5)  # below 0.01 should clamp to 0.01
        assert ct.trade_ratio == 0.01

    def test_pending_queue_when_not_auto_approve(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange, auto_approve=False)

        # Seed a leader directly into test DB
        from bot.database.models import CopyLeader
        leader = CopyLeader(
            external_id="cdc_74935e5e6b816909e70be3b4cd01",
            label="Test Trader",
            allocation_pct=0.1,
            is_active=True,
        )
        test_db.add(leader)
        test_db.commit()

        # Simulate that the exchange returns one trade
        mock_exchange.orders_placed = [
            {
                "id": "trade_001",
                "symbol": "BTC/USDT",
                "side": "buy",
                "amount": 0.1,
                "price": 50000.0,
                "cost": 5000.0,
            }
        ]

        ct.run()

        pending = ct.get_pending_trades()
        assert len(pending) == 1
        assert pending[0]["symbol"] == "BTC/USDT"
        assert pending[0]["side"] == "buy"

    def test_approve_trade(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange, auto_approve=False)

        from bot.database.models import CopyLeader
        leader = CopyLeader(
            external_id="cdc_74935e5e6b816909e70be3b4cd01",
            label="Test Trader",
            allocation_pct=0.1,
            is_active=True,
        )
        test_db.add(leader)
        test_db.commit()

        mock_exchange.orders_placed = [
            {
                "id": "trade_002",
                "symbol": "ETH/USDT",
                "side": "buy",
                "amount": 0.5,
                "price": 3000.0,
                "cost": 1500.0,
            }
        ]

        ct.run()
        pending = ct.get_pending_trades()
        assert len(pending) == 1

        trade_id = pending[0]["id"]
        ct.approve_trade(trade_id)

        assert len(ct.get_pending_trades()) == 0

    def test_reject_trade(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange, auto_approve=False)

        from bot.database.models import CopyLeader
        leader = CopyLeader(
            external_id="cdc_74935e5e6b816909e70be3b4cd01",
            label="Test Trader",
            allocation_pct=0.1,
            is_active=True,
        )
        test_db.add(leader)
        test_db.commit()

        mock_exchange.orders_placed = [
            {
                "id": "trade_003",
                "symbol": "SOL/USDT",
                "side": "sell",
                "amount": 10.0,
                "price": 100.0,
                "cost": 1000.0,
            }
        ]

        ct.run()
        pending = ct.get_pending_trades()
        assert len(pending) == 1

        ok = ct.reject_trade(pending[0]["id"])
        assert ok is True
        assert len(ct.get_pending_trades()) == 0

    def test_reject_nonexistent_returns_false(self, mock_exchange):
        ct = self._make_copy_trader(mock_exchange)
        assert ct.reject_trade("does-not-exist") is False

    def test_get_copy_stats_empty(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange)
        stats = ct.get_copy_stats(days=7)
        assert stats["num_trades"] == 0
        assert stats["win_rate_pct"] == 0.0
        assert stats["total_pnl"] == 0.0

    def test_get_copy_history_empty(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange)
        history = ct.get_copy_history()
        assert history == []

    def test_add_and_list_leader(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange)
        ct.add_leader("cdc_74935e5e6b816909e70be3b4cd01", label="Target Trader", allocation_pct=0.1)
        leaders = ct.get_leaders()
        assert len(leaders) == 1
        assert leaders[0]["external_id"] == "cdc_74935e5e6b816909e70be3b4cd01"
        assert leaders[0]["label"] == "Target Trader"

    def test_remove_leader(self, mock_exchange, test_db):
        ct = self._make_copy_trader(mock_exchange)
        ct.add_leader("cdc_74935e5e6b816909e70be3b4cd01")
        ct.remove_leader("cdc_74935e5e6b816909e70be3b4cd01")
        leaders = ct.get_leaders()
        assert all(not ldr["is_active"] for ldr in leaders)

    def test_inactive_strategy_returns_empty(self, mock_exchange):
        ct = self._make_copy_trader(mock_exchange)
        ct.stop()
        assert ct.run() == []



class TestSignalParsing:
    """Test Telegram signal parsing."""

    def test_parse_buy_signal(self):
        text = "BUY BTC/USDT @ 50000 SL: 48000 TP: 55000"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["symbol"] == "BTC/USDT"
        assert result["action"] == "buy"
        assert result["price"] == 50000.0
        assert result["stop_loss"] == 48000.0
        assert result["take_profit"] == 55000.0

    def test_parse_sell_signal(self):
        text = "SELL ETH/USDT @ 3000 SL: 3100 TP: 2800"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["symbol"] == "ETH/USDT"
        assert result["action"] == "sell"
        assert result["price"] == 3000.0

    def test_parse_long_format(self):
        text = "ETH/USDT LONG Entry: 3000 SL: 2900 TP: 3200"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["action"] == "buy"
        assert result["price"] == 3000.0

    def test_parse_short_format(self):
        text = "BTC/USDT SHORT Entry: 50000 SL: 52000 TP: 45000"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["action"] == "sell"
        assert result["price"] == 50000.0

    def test_parse_signal_format(self):
        text = "Signal: BUY BTCUSDT Price: 50000 SL: 48000 TP: 55000"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["action"] == "buy"
        assert result["price"] == 50000.0

    def test_parse_pair_mapping(self):
        text = "Signal: BUY ETHUSDT Price: 3000"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["symbol"] == "ETH/USDT"

    def test_parse_no_sl_tp(self):
        text = "BUY SOL/USDT @ 100"
        result = SignalFollower.parse_signal(text)
        assert result is not None
        assert result["stop_loss"] is None
        assert result["take_profit"] is None

    def test_parse_invalid_text(self):
        result = SignalFollower.parse_signal("Hello world")
        assert result is None

    def test_parse_empty_text(self):
        result = SignalFollower.parse_signal("")
        assert result is None


class TestSignalFollower:
    """Test signal follower strategy."""

    def test_receive_and_queue(self, mock_exchange):
        from bot.exchange.order_manager import OrderManager
        om = OrderManager.__new__(OrderManager)
        om.client = mock_exchange
        om.risk_manager = None
        om.notifier = None
        om.is_paper = True

        sf = SignalFollower(
            order_manager=om,
            exchange_client=mock_exchange,
            default_amount_usdt=100.0,
        )

        signal = sf.receive_signal("BUY BTC/USDT @ 50000 SL: 48000 TP: 55000")
        assert signal is not None
        assert signal["action"] == "buy"
        assert len(sf._signal_queue) == 1

    def test_inactive_strategy_skips(self, mock_exchange):
        from bot.exchange.order_manager import OrderManager
        om = OrderManager.__new__(OrderManager)
        om.client = mock_exchange
        om.risk_manager = None
        om.notifier = None
        om.is_paper = True

        sf = SignalFollower(
            order_manager=om,
            exchange_client=mock_exchange,
        )
        sf.stop()

        result = sf.run()
        assert result == []
