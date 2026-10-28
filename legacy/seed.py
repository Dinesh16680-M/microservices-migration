"""Fill the legacy SQLite database with a little sample data to migrate."""
import sqlite3

from app import DB_PATH, init_db

init_db()
conn = sqlite3.connect(DB_PATH)
conn.executemany(
    "INSERT INTO accounts (owner, currency) VALUES (?, ?)",
    [("Anna Schmidt", "EUR"), ("Ravi Kumar", "EUR"), ("Lena Weber", "USD")],
)
conn.executemany(
    "INSERT INTO trades (account_id, isin, side, quantity, price) VALUES (?, ?, ?, ?, ?)",
    [
        (1, "DE0005810055", "BUY", 10, 190.50),
        (1, "DE0007164600", "BUY", 5, 120.10),
        (2, "DE0005810055", "SELL", 3, 192.00),
        (3, "US0378331005", "BUY", 8, 225.75),
    ],
)
conn.commit()
conn.close()
print("Seeded", DB_PATH)
