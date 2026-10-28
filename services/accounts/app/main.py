"""Accounts service: owns everything about customer accounts."""
from contextlib import asynccontextmanager
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from .db import get_conn, run_migrations


@asynccontextmanager
async def lifespan(_app: FastAPI):
    run_migrations()
    yield


app = FastAPI(title="Accounts service", version="1.0.0", lifespan=lifespan)
Conn = Annotated[psycopg.Connection, Depends(get_conn)]


class AccountIn(BaseModel):
    owner: str = Field(min_length=1, max_length=200)
    currency: str = Field(pattern="^[A-Z]{3}$", examples=["EUR"])
    legacy_id: int | None = None


class Account(AccountIn):
    id: int


@app.get("/health")
def health():
    return {"status": "ok", "service": "accounts"}


@app.post("/accounts", response_model=Account, status_code=201)
def create_account(account: AccountIn, conn: Conn):
    try:
        return conn.execute(
            "INSERT INTO accounts (owner, currency, legacy_id) VALUES (%s, %s, %s)"
            " RETURNING id, owner, currency, legacy_id",
            (account.owner, account.currency, account.legacy_id),
        ).fetchone()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Account with this legacy_id already exists")


@app.get("/accounts", response_model=list[Account])
def list_accounts(conn: Conn):
    return conn.execute("SELECT id, owner, currency, legacy_id FROM accounts ORDER BY id").fetchall()


@app.get("/accounts/{account_id}", response_model=Account)
def get_account(account_id: int, conn: Conn):
    row = conn.execute(
        "SELECT id, owner, currency, legacy_id FROM accounts WHERE id = %s", (account_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return row
