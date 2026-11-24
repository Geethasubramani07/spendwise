import pandas as pd
import pytest

from app import service


def test_budget_status_thresholds():
    assert service.budget_status(500, 1000) == "ok"
    assert service.budget_status(800, 1000) == "warning"
    assert service.budget_status(1000, 1000) == "warning"
    assert service.budget_status(1001, 1000) == "exceeded"


def test_zero_budget_with_spend_is_exceeded():
    assert service.budget_status(10, 0) == "exceeded"
    assert service.budget_status(0, 0) == "ok"


def test_negative_budget_rejected(conn):
    with pytest.raises(ValueError):
        service.set_budget(conn, "Food", -5)


def test_set_budget_and_summary(conn):
    service.set_budget(conn, "Food", 1000)
    df = pd.DataFrame({"ts": pd.to_datetime(["2026-05-01 12:00", "2026-05-02 13:00"]),
                       "description": ["Swiggy order", "Zomato order"], "amount": [700.0, 400.0]})
    service.import_dataframe(conn, df)
    s = service.monthly_summary(conn, "2026-05")
    food = next(c for c in s["categories"] if c["category"] == "Food")
    assert food["spent"] == 1100.0 and food["status"] == "exceeded"
    assert any("Food" in a for a in s["budget_alerts"])
