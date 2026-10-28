"""Move the data from the legacy SQLite database into the two new services.

It talks to the services only through their APIs, never to their databases directly.
Accounts are created first; their old ids are stored as legacy_id and used to map each
trade to its new account id. Running it twice is safe: existing accounts are skipped.

Usage: python scripts/migrate_data.py legacy/legacy.db
"""
import os
import sqlite3
import sys

import httpx

ACCOUNTS_URL = os.environ.get("ACCOUNTS_URL", "http://localhost:8001")
TRADES_URL = os.environ.get("TRADES_URL", "http://localhost:8002")


def main(db_path: str) -> None:
    legacy = sqlite3.connect(db_path)
    legacy.row_factory = sqlite3.Row

    existing = {a["legacy_id"]: a["id"] for a in httpx.get(f"{ACCOUNTS_URL}/accounts").json()}
    id_map = {}
    for row in legacy.execute("SELECT id, owner, currency FROM accounts"):
        if row["id"] in existing:
            id_map[row["id"]] = existing[row["id"]]
            continue
        response = httpx.post(
            f"{ACCOUNTS_URL}/accounts",
            json={"owner": row["owner"], "currency": row["currency"], "legacy_id": row["id"]},
        )
        response.raise_for_status()
        id_map[row["id"]] = response.json()["id"]
    print(f"Accounts: {len(id_map)} mapped ({len(id_map) - len(existing)} new)")

    if existing:
        print("Accounts were already migrated, skipping trades to avoid duplicates.")
        return

    count = 0
    for row in legacy.execute("SELECT account_id, isin, side, quantity, price FROM trades"):
        response = httpx.post(
            f"{TRADES_URL}/trades",
            json={
                "account_id": id_map[row["account_id"]],
                "isin": row["isin"],
                "side": row["side"],
                "quantity": row["quantity"],
                "price": str(row["price"]),
            },
        )
        response.raise_for_status()
        count += 1
    print(f"Trades: {count} migrated")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "legacy/legacy.db")
