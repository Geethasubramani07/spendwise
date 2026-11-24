import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import get_conn  # noqa: E402


@pytest.fixture()
def conn(tmp_path):
    c = get_conn(str(tmp_path / "test.db"))
    yield c
    c.close()


@pytest.fixture()
def api_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SPENDWISE_DB", str(tmp_path / "api.db"))
    monkeypatch.setenv("ADMIN_TOKEN", "test-token")
