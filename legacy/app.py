"""The "legacy" monolith: accounts and trades in one Flask app and one SQLite file.

This is the starting point of the migration. It works, but every change to trades
means redeploying accounts too, and SQLite can't be shared by several servers.
"""
import sqlite3

from flask import Flask, g, jsonify, request

DB_PATH = "legacy.db"
app = Flask(__name__)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner TEXT NOT NULL,
            currency TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL REFERENCES accounts(id),
            isin TEXT NOT NULL,
            side TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL
        );
        """
    )
    conn.commit()
    conn.close()


@app.post("/accounts")
def create_account():
    data = request.get_json()
    cur = db().execute(
        "INSERT INTO accounts (owner, currency) VALUES (?, ?)", (data["owner"], data["currency"])
    )
    db().commit()
    return jsonify(id=cur.lastrowid, **data), 201


@app.get("/accounts")
def list_accounts():
    rows = db().execute("SELECT * FROM accounts").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/trades")
def create_trade():
    data = request.get_json()
    cur = db().execute(
        "INSERT INTO trades (account_id, isin, side, quantity, price) VALUES (?, ?, ?, ?, ?)",
        (data["account_id"], data["isin"], data["side"], data["quantity"], data["price"]),
    )
    db().commit()
    return jsonify(id=cur.lastrowid, **data), 201


@app.get("/trades")
def list_trades():
    rows = db().execute("SELECT * FROM trades").fetchall()
    return jsonify([dict(r) for r in rows])


if __name__ == "__main__":
    init_db()
    app.run(port=5000)
