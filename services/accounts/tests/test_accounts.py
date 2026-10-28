def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "service": "accounts"}


def test_create_and_get_account(client):
    created = client.post("/accounts", json={"owner": "Anna Schmidt", "currency": "EUR"})
    assert created.status_code == 201
    account_id = created.json()["id"]

    fetched = client.get(f"/accounts/{account_id}")
    assert fetched.status_code == 200
    assert fetched.json()["owner"] == "Anna Schmidt"


def test_unknown_account_returns_404(client):
    assert client.get("/accounts/9999").status_code == 404


def test_invalid_currency_is_rejected(client):
    response = client.post("/accounts", json={"owner": "Anna", "currency": "euro"})
    assert response.status_code == 422


def test_duplicate_legacy_id_returns_409(client):
    body = {"owner": "Anna", "currency": "EUR", "legacy_id": 1}
    assert client.post("/accounts", json=body).status_code == 201
    assert client.post("/accounts", json=body).status_code == 409
