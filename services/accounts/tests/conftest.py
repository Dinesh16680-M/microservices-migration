import pytest
from fastapi.testclient import TestClient

from app.db import connect
from app.main import app


@pytest.fixture()
def client():
    # Entering the client runs the lifespan, which applies the migrations.
    with TestClient(app) as c:
        with connect() as conn:
            conn.execute("TRUNCATE accounts RESTART IDENTITY")
        yield c
