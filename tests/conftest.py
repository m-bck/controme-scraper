import pytest
import keyring

from controme_scraper.controller import ContromeController


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: marks tests as integration tests requiring a live Controme system")


@pytest.fixture(scope="session")
def controller():
    host = keyring.get_password("controme_scraper", "host")
    user = keyring.get_password("controme_scraper", "user")
    password = keyring.get_password("controme_scraper", "password")

    if not all([host, user, password]):
        pytest.skip("Controme credentials not found in keyring — skipping integration tests")

    return ContromeController(host=host, username=user, password=password)
