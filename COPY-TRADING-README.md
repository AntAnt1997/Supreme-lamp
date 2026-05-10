# Copy Trading Bot — Complete Guide

Mirror the trades of trader **`cdc_74935e5e6b816909e70be3b4cd01`** automatically,
integrated with the 24/7 AI Production Workers system.

---

## Table of Contents

1. [Overview](#overview)
2. [How It Works](#how-it-works)
3. [Setup & Configuration](#setup--configuration)
4. [API Reference](#api-reference)
5. [Dashboard](#dashboard)
6. [Risk Management](#risk-management)
7. [Troubleshooting](#troubleshooting)
8. [Performance Tracking](#performance-tracking)

---

## Overview

The copy trading bot automatically detects new trades from the configured trader
and either executes them immediately (**auto-approve**) or queues them for manual
review (**approval workflow**).

### Key Features

- Polls the target trader every 30 seconds (configurable)
- Proportional position sizing via `COPY_TRADE_RATIO`
- Per-trade minimum (`COPY_MIN_TRADE_USDT`) and maximum (`COPY_MAX_TRADE_USDT`) caps
- Manual approval workflow or fully automatic execution
- Real-time notifications via Telegram
- React dashboard with live status, pending approvals, position management, and 7-day statistics

---

## How It Works

```
1. Bot polls trader cdc_74935e5e6b816909e70be3b4cd01 every 30 s
2. New trade detected → check against filters (min/max size)
3. Calculate copy amount = min(balance × allocation_pct, leader_amount × ratio)
4a. auto_approve=true  → execute immediately
4b. auto_approve=false → queue for approval (shown in dashboard / Telegram)
5. Positions tracked with stop-loss and take-profit via the risk manager
6. On exit: mirror exit OR hit stop-loss/take-profit automatically
```

### Example Flow

```
Trader buys $10,000 ETH at $2,000
  → Bot detects trade
  → Your copy: $1,000 ETH (10% ratio)
  → Price drops to $1,800 (-10%) → auto stop-loss triggered
  OR
  → Price rises to $2,500 (+25%) → auto take-profit triggered
```

---

## Setup & Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Copy Trading
COPY_TRADER_IDS=cdc_74935e5e6b816909e70be3b4cd01   # pre-seeded automatically
COPY_TRADE_RATIO=0.1          # 10% of their size
COPY_MIN_TRADE_USDT=50        # skip trades smaller than $50
COPY_MAX_TRADE_USDT=5000      # cap at $5,000 per trade
COPY_AUTO_APPROVE=false       # start with manual approval
COPY_POLL_INTERVAL_SEC=30     # poll every 30 seconds
```

### 2. Recommended Starting Settings (Conservative)

```bash
COPY_TRADE_RATIO=0.05         # 5% of their size
COPY_MIN_TRADE_USDT=50
COPY_MAX_TRADE_USDT=1000
COPY_AUTO_APPROVE=false       # review every trade
```

### 3. Start the Bot

```bash
# Start the full system (copy trader runs automatically)
python -m bot.main

# Or via the API after the server is running:
curl -X POST http://localhost:8080/api/strategies/copy/start
```

### 4. Scaling Up

After one week of monitoring:

1. Increase `COPY_TRADE_RATIO` by 5% weekly
2. Enable `COPY_AUTO_APPROVE=true` when confident
3. Adjust `COPY_MIN_TRADE_USDT` / `COPY_MAX_TRADE_USDT` based on account size

---

## API Reference

All endpoints are served by the FastAPI dashboard at `http://localhost:8080`.

### Leaders

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/leaders` | List all copy leaders |
| `POST` | `/api/leaders` | Add a new leader |
| `DELETE` | `/api/leaders/{external_id}` | Deactivate a leader |

**Add leader body:**
```json
{
  "external_id": "cdc_74935e5e6b816909e70be3b4cd01",
  "label": "Target Trader",
  "allocation_pct": 0.1
}
```

### Configuration

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/copy-trading/config` | Get current config |
| `PATCH` | `/api/copy-trading/config` | Update config at runtime |

**Update config body (all fields optional):**
```json
{
  "trade_ratio": 0.1,
  "min_trade_usdt": 50,
  "max_trade_usdt": 5000,
  "auto_approve": false
}
```

### Pending Approvals

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/copy-trading/pending` | List trades awaiting approval |
| `POST` | `/api/copy-trading/pending/{id}/approve` | Execute a pending trade |
| `POST` | `/api/copy-trading/pending/{id}/reject` | Discard a pending trade |

### Statistics & History

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/copy-trading/stats?days=7` | 7-day win rate, PnL, volume |
| `GET` | `/api/copy-trading/history?limit=50` | Recent copy trade records |

### Bot Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/strategies/copy/start` | Start the copy trader |
| `POST` | `/api/strategies/copy/stop` | Stop the copy trader |
| `GET` | `/api/strategies/status` | All strategy statuses |

### Position Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/portfolio/positions` | All open positions |
| `POST` | `/api/positions/{id}/close` | Close a specific position |

---

## Dashboard

Open the React dashboard (served on port `5173` in dev or the built frontend):

- **Bot Status** — ACTIVE / STOPPED with one-click toggle
- **7-day Stats** — win rate, total PnL, volume
- **Configuration panel** — copy ratio slider, min/max trade size, auto-approve toggle
- **Pending Approvals** — approve or reject each detected trade
- **Open Positions** — real-time PnL with close buttons
- **Tracked Leaders** — allocation, trade count, cumulative PnL
- **Trade History** — paginated table of all copy trades

Data refreshes automatically every **5 seconds**.

---

## Risk Management

The copy trader integrates with all existing safety rails:

1. **Trade Filters**
   - Minimum trade size (`COPY_MIN_TRADE_USDT`) — skips noise trades
   - Maximum trade size (`COPY_MAX_TRADE_USDT`) — caps exposure per trade

2. **Position Limits**
   - `MAX_POSITIONS` — global cap across all strategies
   - `MAX_POSITION_SIZE_PCT` — single position cap as % of portfolio

3. **Automatic Exits**
   - Stop-loss at `STOP_LOSS_PCT` (default -3%)
   - Take-profit at `TAKE_PROFIT_PCT` (default +6%)
   - Trailing stop at `TRAILING_STOP_PCT`

4. **Daily Loss Limit**
   - Bot halts trading if daily loss exceeds `DAILY_LOSS_LIMIT_PCT`

5. **Kill Switch**
   - `POST /api/strategies/copy/stop` instantly pauses all copy trading

---

## Troubleshooting

### Bot detects no trades

- Ensure the leader's exchange account is accessible from the configured API key
- Check `COPY_POLL_INTERVAL_SEC` — default 30 s
- Verify the leader is `is_active=true` via `GET /api/leaders`

### Trades queued but not executed

- `COPY_AUTO_APPROVE=false` — approve via dashboard or API
- Set `COPY_AUTO_APPROVE=true` in `.env` and restart, or `PATCH /api/copy-trading/config`

### Trade value too small / skipped

- Lower `COPY_MIN_TRADE_USDT` in config

### Trade capped below expected size

- Raise `COPY_MAX_TRADE_USDT` — default $5,000

---

## Performance Tracking

Statistics endpoint (`GET /api/copy-trading/stats?days=7`) returns:

```json
{
  "period_days": 7,
  "num_trades": 12,
  "closed_trades": 10,
  "wins": 7,
  "win_rate_pct": 70.0,
  "total_pnl": 342.50,
  "total_volume_usdt": 18500.00
}
```

Use these to evaluate performance and adjust `COPY_TRADE_RATIO` accordingly:

| Win Rate | Suggested Action |
|----------|-----------------|
| < 40%    | Reduce ratio, review leader |
| 40–60%   | Hold current settings |
| > 60%    | Gradually increase ratio |
