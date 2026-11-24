"""API tests. Need fastapi + httpx (pip install -r requirements.txt); skipped if missing."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture()
def client(api_db):
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_demo_summary_alerts_flow(client):
    r = client.post("/api/transactions/demo")
    assert r.status_code == 200 and r.json()["imported"] > 100
    s = client.get("/api/summary").json()
    assert s["transactions"] > 0 and s["fraud_alerts"] >= 0
    alerts = client.get("/api/alerts").json()
    assert all(a["reason"] for a in alerts)


def test_csv_import_and_bad_file(client):
    good = b"date,description,amount\n2026-05-01 10:00,Swiggy,300\n"
    ok = client.post("/api/transactions/import", files={"file": ("t.csv", good, "text/csv")})
    assert ok.status_code == 200 and ok.json()["imported"] == 1
    bad = client.post("/api/transactions/import", files={"file": ("t.csv", b"a,b\n1,2\n", "text/csv")})
    assert bad.status_code == 400


def test_budget_update_validation(client):
    assert client.put("/api/budgets/Food", json={"monthly_limit": 1234}).status_code == 200
    assert client.put("/api/budgets/Food", json={"monthly_limit": -1}).status_code == 422
    assert client.put("/api/budgets/Nope", json={"monthly_limit": 10}).status_code == 404


def test_admin_endpoints_need_token(client):
    assert client.delete("/api/transactions").status_code == 403
    assert client.delete("/api/transactions", headers={"X-Admin-Token": "test-token"}).status_code == 200
