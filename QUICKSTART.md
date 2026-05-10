# WalletTrack Quick Start

Track crypto portfolios across 6+ blockchains in minutes.

## Prerequisites

- Python 3.11+ with project dependencies (`pip install -r requirements.txt`)
- Node.js 18+ for the frontend

---

## 1. Get an Alchemy API Key (free)

1. Go to [alchemy.com](https://www.alchemy.com/) and create a free account.
2. Create a new app → copy the **API Key**.

## 2. Configure

```bash
cp .env.example .env
# Set ALCHEMY_API_KEY=<your key> in .env
```

## 3. Run the backend

```bash
python -m bot.main
# Dashboard available at http://localhost:8080
```

## 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173/wallets
```

## 5. Add your first wallet

- Open **http://localhost:5173/wallets**
- Click **+ Add Wallet**
- Paste an EVM address and select a chain
- Click **Sync Now** to fetch live balances

## 6. Import from Polymarket

```bash
# Edit scripts/example_wallets.json with your trader addresses
python scripts/polymarket_import.py \
  --bot-data scripts/example_wallets.json \
  --api-url http://localhost:8080 \
  --auto-sync
```

---

## Supported Chains

| Chain    | Native Token |
|----------|-------------|
| Ethereum | ETH         |
| Polygon  | MATIC       |
| Arbitrum | ETH         |
| Base     | ETH         |
| Optimism | ETH         |
| BNB Chain| BNB         |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/wallets` | List tracked wallets |
| POST | `/api/wallets` | Add wallet |
| GET | `/api/wallets/{id}` | Get wallet details |
| PATCH | `/api/wallets/{id}` | Update wallet |
| DELETE | `/api/wallets/{id}` | Remove wallet |
| POST | `/api/wallets/{id}/sync` | Sync from blockchain |
| GET | `/api/wallets/{id}/tokens` | Token holdings |
| GET | `/api/wallets/{id}/transactions` | Transaction history |
| GET | `/api/wallets/{id}/history` | Portfolio value history |
| GET | `/api/wallets/portfolio/summary` | Aggregate summary |
| POST | `/api/polymarket/import` | Bulk import wallets |
