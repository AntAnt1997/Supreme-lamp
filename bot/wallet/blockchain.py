"""Blockchain data fetching via Alchemy API and CoinGecko price data."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── Chain configuration ───────────────────────────────────────────────────────

CHAIN_CONFIG: dict[str, dict[str, Any]] = {
    "ethereum": {
        "native_symbol": "ETH",
        "native_name": "Ethereum",
        "coingecko_id": "ethereum",
        "alchemy_network": "eth-mainnet",
    },
    "polygon": {
        "native_symbol": "MATIC",
        "native_name": "Polygon",
        "coingecko_id": "matic-network",
        "alchemy_network": "polygon-mainnet",
    },
    "arbitrum": {
        "native_symbol": "ETH",
        "native_name": "Ethereum (Arbitrum)",
        "coingecko_id": "ethereum",
        "alchemy_network": "arb-mainnet",
    },
    "base": {
        "native_symbol": "ETH",
        "native_name": "Ethereum (Base)",
        "coingecko_id": "ethereum",
        "alchemy_network": "base-mainnet",
    },
    "optimism": {
        "native_symbol": "ETH",
        "native_name": "Ethereum (Optimism)",
        "coingecko_id": "ethereum",
        "alchemy_network": "opt-mainnet",
    },
    "bsc": {
        "native_symbol": "BNB",
        "native_name": "BNB Chain",
        "coingecko_id": "binancecoin",
        "alchemy_network": None,  # BSC uses public RPC
    },
}

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
# Simple in-memory price cache to avoid hammering CoinGecko
_price_cache: dict[str, tuple[float, float]] = {}  # coin_id -> (price_usd, fetched_at)
_PRICE_CACHE_TTL = 60  # seconds


class BlockchainService:
    """Fetches wallet balances and transactions using Alchemy and CoinGecko."""

    def __init__(self, alchemy_api_key: str | None = None) -> None:
        self.api_key = alchemy_api_key or os.getenv("ALCHEMY_API_KEY", "")

    # ── Price helpers ─────────────────────────────────────────────────────────

    def _get_prices(self, coin_ids: list[str]) -> dict[str, float]:
        """Return USD prices for a list of CoinGecko coin IDs (cached)."""
        if not coin_ids:
            return {}

        now = time.time()
        missing = [cid for cid in coin_ids if cid not in _price_cache or now - _price_cache[cid][1] > _PRICE_CACHE_TTL]

        if missing:
            ids_str = ",".join(missing)
            try:
                resp = requests.get(
                    f"{COINGECKO_BASE}/simple/price",
                    params={"ids": ids_str, "vs_currencies": "usd"},
                    timeout=10,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for cid, v in data.items():
                        _price_cache[cid] = (v.get("usd", 0.0), now)
                else:
                    logger.warning("CoinGecko price fetch failed: %s", resp.status_code)
            except Exception as exc:
                logger.warning("CoinGecko request error: %s", exc)

        return {cid: _price_cache[cid][0] for cid in coin_ids if cid in _price_cache}

    def get_native_price_usd(self, chain: str) -> float:
        """Return the current USD price of the native token for a chain."""
        cfg = CHAIN_CONFIG.get(chain)
        if not cfg:
            return 0.0
        prices = self._get_prices([cfg["coingecko_id"]])
        return prices.get(cfg["coingecko_id"], 0.0)

    # ── Alchemy helpers ───────────────────────────────────────────────────────

    def _alchemy_url(self, chain: str) -> str | None:
        cfg = CHAIN_CONFIG.get(chain)
        if not cfg or not cfg.get("alchemy_network"):
            return None
        if not self.api_key:
            return None
        return f"https://{cfg['alchemy_network']}.g.alchemy.com/v2/{self.api_key}"

    def _alchemy_post(self, chain: str, method: str, params: list) -> Any:
        url = self._alchemy_url(chain)
        if not url:
            raise ValueError(f"Alchemy not available for chain '{chain}' or no API key configured.")
        payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise RuntimeError(f"Alchemy error: {data['error']}")
        return data.get("result")

    def _alchemy_nft_url(self, chain: str) -> str | None:
        cfg = CHAIN_CONFIG.get(chain)
        if not cfg or not cfg.get("alchemy_network") or not self.api_key:
            return None
        return f"https://{cfg['alchemy_network']}.g.alchemy.com/v3/{self.api_key}"

    # ── Public API ────────────────────────────────────────────────────────────

    def get_native_balance(self, address: str, chain: str) -> dict[str, Any]:
        """Return native token balance in both raw units and USD."""
        cfg = CHAIN_CONFIG.get(chain, {})
        native_symbol = cfg.get("native_symbol", "ETH")

        try:
            hex_balance = self._alchemy_post(chain, "eth_getBalance", [address, "latest"])
            balance_wei = int(hex_balance, 16)
            balance = balance_wei / 1e18
        except Exception as exc:
            logger.warning("Failed to fetch native balance for %s on %s: %s", address, chain, exc)
            balance = 0.0

        price = self.get_native_price_usd(chain)
        return {
            "symbol": native_symbol,
            "name": cfg.get("native_name", native_symbol),
            "balance": balance,
            "price_usd": price,
            "balance_usd": balance * price,
            "token_address": None,
        }

    def get_token_balances(self, address: str, chain: str) -> list[dict[str, Any]]:
        """Return ERC-20 token balances for the address using Alchemy's token API."""
        try:
            result = self._alchemy_post(
                chain,
                "alchemy_getTokenBalances",
                [address, "erc20"],
            )
            raw_balances = result.get("tokenBalances", []) if isinstance(result, dict) else []
        except Exception as exc:
            logger.warning("Failed to fetch token balances for %s on %s: %s", address, chain, exc)
            return []

        # Filter out zero balances
        non_zero = [tb for tb in raw_balances if tb.get("tokenBalance") not in (None, "0x0000000000000000000000000000000000000000000000000000000000000000")]

        tokens: list[dict[str, Any]] = []
        for tb in non_zero[:50]:  # cap at 50 tokens
            contract = tb.get("contractAddress", "")
            raw_bal = tb.get("tokenBalance", "0x0")
            try:
                raw_int = int(raw_bal, 16)
            except (ValueError, TypeError):
                continue
            if raw_int == 0:
                continue

            # Fetch metadata
            try:
                meta = self._alchemy_post(chain, "alchemy_getTokenMetadata", [contract])
                decimals = meta.get("decimals") or 18
                symbol = meta.get("symbol") or "UNKNOWN"
                name = meta.get("name") or symbol
            except Exception:
                decimals = 18
                symbol = "UNKNOWN"
                name = "Unknown Token"

            balance = raw_int / (10 ** decimals)
            tokens.append({
                "symbol": symbol,
                "name": name,
                "balance": balance,
                "token_address": contract,
                "price_usd": 0.0,
                "balance_usd": 0.0,
            })

        return tokens

    def get_transactions(self, address: str, chain: str, max_count: int = 100) -> list[dict[str, Any]]:
        """Return recent transactions for a wallet address."""
        try:
            result = self._alchemy_post(
                chain,
                "alchemy_getAssetTransfers",
                [{
                    "fromAddress": address,
                    "category": ["external", "erc20", "erc721", "erc1155"],
                    "maxCount": hex(min(max_count, 1000)),
                    "withMetadata": True,
                    "order": "desc",
                }],
            )
            transfers_out = result.get("transfers", []) if result else []
        except Exception as exc:
            logger.warning("Failed to fetch outbound txns for %s on %s: %s", address, chain, exc)
            transfers_out = []

        try:
            result_in = self._alchemy_post(
                chain,
                "alchemy_getAssetTransfers",
                [{
                    "toAddress": address,
                    "category": ["external", "erc20", "erc721", "erc1155"],
                    "maxCount": hex(min(max_count, 1000)),
                    "withMetadata": True,
                    "order": "desc",
                }],
            )
            transfers_in = result_in.get("transfers", []) if result_in else []
        except Exception as exc:
            logger.warning("Failed to fetch inbound txns for %s on %s: %s", address, chain, exc)
            transfers_in = []

        seen_hashes: set[str] = set()
        txns: list[dict[str, Any]] = []
        addr_lower = address.lower()

        for tx in transfers_out + transfers_in:
            tx_hash = tx.get("hash", "")
            if tx_hash in seen_hashes:
                continue
            seen_hashes.add(tx_hash)

            from_addr = (tx.get("from") or "").lower()
            to_addr = (tx.get("to") or "").lower()
            if from_addr == addr_lower:
                tx_type = "send"
            elif to_addr == addr_lower:
                tx_type = "receive"
            else:
                tx_type = "contract"

            raw_ts = tx.get("metadata", {}).get("blockTimestamp")
            ts: datetime | None = None
            if raw_ts:
                try:
                    ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    ts = None

            value = tx.get("value") or 0.0
            txns.append({
                "tx_hash": tx_hash,
                "block_number": tx.get("blockNum"),
                "tx_type": tx_type,
                "from_address": tx.get("from"),
                "to_address": tx.get("to"),
                "asset": tx.get("asset") or "",
                "value": float(value),
                "value_usd": float(tx.get("value") or 0.0),  # Alchemy doesn't give USD; use raw
                "gas_used": None,
                "gas_price_gwei": None,
                "fee_usd": None,
                "status": "success",
                "timestamp": ts,
            })

        # Sort newest first
        txns.sort(key=lambda t: t["timestamp"] or datetime.min, reverse=True)
        return txns[:max_count]

    def sync_wallet(self, address: str, chain: str) -> dict[str, Any]:
        """Fetch native balance, token balances, and recent transactions for a wallet."""
        native = self.get_native_balance(address, chain)
        tokens = self.get_token_balances(address, chain)
        transactions = self.get_transactions(address, chain)

        all_holdings = [native] + tokens
        total_usd = sum(h.get("balance_usd", 0.0) for h in all_holdings)

        return {
            "address": address,
            "chain": chain,
            "native": native,
            "tokens": tokens,
            "transactions": transactions,
            "total_value_usd": total_usd,
            "synced_at": datetime.now(timezone.utc).replace(tzinfo=None),
        }
