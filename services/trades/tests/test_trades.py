TRADE = {"account_id": 1, "isin": "DE0005810055", "side": "BUY", "quantity": 10, "price": "190.50"}


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "trades"}


def test_create_trade_for_known_account(client):
    response = client.post("/trades", json=TRADE)
    assert response.status_code == 201
    assert response.json()["isin"] == "DE0005810055"


def test_unknown_account_is_rejected(client):
    response = client.post("/trades", json={**TRADE, "account_id": 42})
    assert response.status_code == 422
    assert response.json()["detail"] == "Unknown account_id"


def test_invalid_isin_and_quantity_are_rejected(client):
    assert client.post("/trades", json={**TRADE, "isin": "NOT-AN-ISIN"}).status_code == 422
    assert client.post("/trades", json={**TRADE, "quantity": 0}).status_code == 422


def test_list_trades_filtered_by_account(client):
    client.post("/trades", json=TRADE)
    client.post("/trades", json={**TRADE, "account_id": 2, "side": "SELL"})

    trades = client.get("/trades", params={"account_id": 2}).json()
    assert len(trades) == 1
    assert trades[0]["side"] == "SELL"


def test_accounts_service_down_returns_503(client):
    import httpx

    from app.accounts_client import get_accounts_client
    from app.main import app

    class DownAccountsClient:
        def account_exists(self, account_id: int) -> bool:
            raise httpx.ConnectError("accounts service is down")

    app.dependency_overrides[get_accounts_client] = DownAccountsClient
    assert client.post("/trades", json=TRADE).status_code == 503
