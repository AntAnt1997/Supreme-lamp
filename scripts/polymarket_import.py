#!/usr/bin/env python3
"""
Polymarket wallet import script.

Reads a JSON file containing Polymarket trader wallets (exported from a signal bot)
and imports them into the WalletTrack API.

Usage:
    python polymarket_import.py --bot-data wallets.json --api-url http://localhost:8080
    python polymarket_import.py --bot-data wallets.json --api-url http://localhost:8080 --auto-sync
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests


def load_wallet_data(path: str) -> list[dict]:
    """Load wallet data from a JSON file."""
    file = Path(path)
    if not file.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(1)
    with file.open() as f:
        data = json.load(f)
    # Support both {"tracked_wallets": [...]} and a bare list
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "tracked_wallets" in data:
        return data["tracked_wallets"]
    print("[ERROR] Unexpected JSON format. Expected list or {\"tracked_wallets\": [...]}", file=sys.stderr)
    sys.exit(1)


def import_wallets(api_url: str, wallets: list[dict]) -> dict:
    """POST wallets to the /api/polymarket/import endpoint."""
    url = api_url.rstrip("/") + "/api/polymarket/import"
    payload = {"tracked_wallets": wallets}
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def sync_all_wallets(api_url: str) -> None:
    """Trigger a sync for every tracked wallet."""
    list_url = api_url.rstrip("/") + "/api/wallets"
    wallets = requests.get(list_url, timeout=10).json()
    if not isinstance(wallets, list):
        print("[WARN] Could not fetch wallet list for auto-sync.")
        return
    for w in wallets:
        wid = w.get("id")
        if not wid:
            continue
        sync_url = f"{api_url.rstrip('/')}/api/wallets/{wid}/sync"
        try:
            resp = requests.post(sync_url, timeout=30)
            resp.raise_for_status()
            result = resp.json()
            print(f"  ✓ Synced wallet {wid} ({w.get('address', '')[:10]}...) — "
                  f"${result.get('total_value_usd', 0):.2f} USD")
        except Exception as e:
            print(f"  ✗ Sync failed for wallet {wid}: {e}")
        time.sleep(0.5)  # gentle rate-limiting


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Polymarket wallets into WalletTrack")
    parser.add_argument("--bot-data", required=True, help="Path to JSON file with wallet data")
    parser.add_argument("--api-url", default="http://localhost:8080", help="WalletTrack API base URL")
    parser.add_argument("--auto-sync", action="store_true", help="Sync all wallets after import")
    args = parser.parse_args()

    print(f"Loading wallets from {args.bot_data}...")
    wallets = load_wallet_data(args.bot_data)
    print(f"Found {len(wallets)} wallet(s). Importing to {args.api_url}...")

    result = import_wallets(args.api_url, wallets)
    added = result.get("added", 0)
    skipped = result.get("skipped", 0)
    errors = result.get("errors", [])

    print(f"\nImport complete:")
    print(f"  ✓ Added:   {added}")
    print(f"  ~ Skipped: {skipped} (already tracked)")
    if errors:
        print(f"  ✗ Errors:  {len(errors)}")
        for err in errors:
            print(f"    - {err}")

    if args.auto_sync and added > 0:
        print("\nAuto-syncing wallets...")
        sync_all_wallets(args.api_url)

    print("\nDone! Open the WalletTrack dashboard to view your wallets.")


if __name__ == "__main__":
    main()
