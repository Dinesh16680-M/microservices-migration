"""Trades service: records buy and sell orders for existing accounts."""
from contextlib import asynccontextmanager
from decimal import Decimal
from typing import Annotated, Literal

import httpx
import psycopg
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .accounts_client import AccountsClient, get_accounts_client
from .db import get_conn, run_migrations


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="Trades service", version="1.0.0", lifespan=lifespan)
Conn = Annotated[psycopg.Connection, Depends(get_conn)]
Accounts = Annotated[AccountsClient, Depends(get_accounts_client)]


class TradeIn(BaseModel):
    account_id: int
    isin: str = Field(pattern="^[A-Z]{2}[A-Z0-9]{9}[0-9]$", examples=["DE0005810055"])
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: Decimal = Field(gt=0, max_digits=14, decimal_places=4)


class Trade(TradeIn):
    id: int


@app.get("/health")
def health():
    return {"status": "ok", "service": "trades"}


@app.post("/trades", response_model=Trade, status_code=201)
def create_trade(trade: TradeIn, conn: Conn, accounts: Accounts):
    try:
        exists = accounts.account_exists(trade.account_id)
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Accounts service unavailable")
    if not exists:
        raise HTTPException(status_code=422, detail="Unknown account_id")

    return conn.execute(
        "INSERT INTO trades (account_id, isin, side, quantity, price) VALUES (%s, %s, %s, %s, %s)"
        " RETURNING id, account_id, isin, side, quantity, price",
        (trade.account_id, trade.isin, trade.side, trade.quantity, trade.price),
    ).fetchone()


@app.get("/trades", response_model=list[Trade])
def list_trades(conn: Conn, account_id: int | None = None):
    if account_id is None:
        return conn.execute(
            "SELECT id, account_id, isin, side, quantity, price FROM trades ORDER BY id"
        ).fetchall()
    return conn.execute(
        "SELECT id, account_id, isin, side, quantity, price FROM trades WHERE account_id = %s ORDER BY id",
        (account_id,),
    ).fetchall()
