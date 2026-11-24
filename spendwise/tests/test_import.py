import pytest

from app import service

GOOD = b"date,description,amount\n2026-05-01 10:00,UPI/Swiggy/111,350\n2026-05-02 11:00,Uber trip 22,180.5\n"


def test_parse_good_csv():
    df = service.parse_csv(GOOD)
    assert len(df) == 2 and df.attrs["skipped"] == 0


def test_missing_column_rejected():
    with pytest.raises(service.ImportError_):
        service.parse_csv(b"date,amount\n2026-05-01,10\n")


def test_bad_rows_are_skipped_not_fatal():
    raw = b"date,description,amount\nnot-a-date,Swiggy,100\n2026-05-01,Swiggy,abc\n2026-05-01,Swiggy,-5\n2026-05-01,Swiggy,50\n"
    df = service.parse_csv(raw)
    assert len(df) == 1 and df.attrs["skipped"] == 3


def test_import_categorises_and_dedupes(conn):
    df = service.parse_csv(GOOD)
    first = service.import_dataframe(conn, df)
    second = service.import_dataframe(conn, df)
    assert first["imported"] == 2 and second["imported"] == 0 and second["duplicates"] == 2
    cats = {r["description"]: r["category"] for r in service.list_transactions(conn)}
    assert cats["UPI/Swiggy/111"] == "Food" and cats["Uber trip 22"] == "Transport"


def test_demo_end_to_end_raises_alerts(conn):
    result = service.load_demo(conn, days=120)
    assert result["imported"] > 200
    assert result["alerts"] > 0
    assert all(a["reason"] for a in service.alerts(conn))
