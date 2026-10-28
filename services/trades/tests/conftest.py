import pytest
from fastapi.testclient import TestClient

from app.accounts_client import get_accounts_client
from app.db import connect
from app.main import app


class FakeAccountsClient:
    """Stands in for the accounts service, so these tests don't need it running."""

    known_ids = {1, 2}

    def account_exists(self, account_id: int) -> bool:
        return account_id in self.known_ids


@pytest.fixture()
def client():
    app.dependency_overrides[get_accounts_client] = FakeAccountsClient
    with TestClient(app) as c:
        with connect() as conn:
            conn.execute("TRUNCATE trades RESTART IDENTITY")
        yield c
    app.dependency_overrides.clear()
