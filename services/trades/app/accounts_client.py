"""Small HTTP client for the accounts service."""
import os

import httpx

ACCOUNTS_URL = os.environ.get("ACCOUNTS_URL", "http://localhost:8001")


class AccountsClient:
    def __init__(self, base_url: str = ACCOUNTS_URL):
        self.base_url = base_url

    def account_exists(self, account_id: int) -> bool:
        response = httpx.get(f"{self.base_url}/accounts/{account_id}", timeout=3.0)
        if response.status_code == 404:
            return False
        response.raise_for_status()
        return True


def get_accounts_client() -> AccountsClient:
    return AccountsClient()
