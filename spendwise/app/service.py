"""Import, budgets and reporting. No web framework in here, so it is easy to unit-test."""
from __future__ import annotations

import hashlib
import io
import sqlite3
from datetime import datetime

import pandas as pd

from .categoriser import get_categoriser, normalize_merchant
from .fraud import detect
from .synthetic import make_transactions

REQUIRED_COLUMNS = {"date", "description", "amount"}
MAX_ROWS = 50_000


class ImportError_(ValueError):
    """Raised for bad CSV input (shown to the user as a 400 error)."""


def parse_csv(raw: bytes) -> pd.DataFrame:
    try:
        df = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise ImportError_(f"Could not read CSV: {exc}") from exc
    df.columns = [str(c).strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ImportError_(f"Missing column(s): {', '.join(sorted(missing))}. Need: date, description, amount")
    if len(df) > MAX_ROWS:
        raise ImportError_(f"Too many rows (max {MAX_ROWS})")
    df = df[["date", "description", "amount"]].copy()
    df["ts"] = pd.to_datetime(df["date"], errors="coerce", format="mixed")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df["description"] = df["description"].astype(str).str.strip()
    bad = df["ts"].isna() | df["amount"].isna() | (df["description"] == "") | (df["amount"] <= 0)
    df.attrs["skipped"] = int(bad.sum())
    return df.loc[~bad, ["ts", "description", "amount"]].reset_index(drop=True)


def _fingerprint(ts, description, amount) -> str:
    return hashlib.sha256(f"{ts}|{description}|{amount:.2f}".encode()).hexdigest()


def import_dataframe(conn: sqlite3.Connection, df: pd.DataFrame, skipped: int = 0) -> dict:
    """Categorise, de-duplicate, store, then re-run fraud detection on all history."""
    cat = get_categoriser()
    inserted = duplicates = 0
    categories = cat.predict_many(df["description"].tolist())
    for (_, r), c in zip(df.iterrows(), categories):
        ts = pd.Timestamp(r["ts"]).strftime("%Y-%m-%d %H:%M:%S")
        fp = _fingerprint(ts, r["description"], float(r["amount"]))
        try:
            conn.execute(
                "INSERT INTO transactions(ts, description, merchant, amount, category, fingerprint)"
                " VALUES (?,?,?,?,?,?)",
                (ts, r["description"], normalize_merchant(r["description"]), float(r["amount"]), c, fp),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            duplicates += 1
    conn.commit()
    flagged = run_detection(conn)
    return {"imported": inserted, "duplicates": duplicates, "skipped": skipped, "alerts": flagged}


def run_detection(conn: sqlite3.Connection) -> int:
    rows = conn.execute("SELECT id, ts, description, amount, category FROM transactions").fetchall()
    if not rows:
        return 0
    df = pd.DataFrame([dict(r) for r in rows])
    res = detect(df)
    conn.executemany(
        "UPDATE transactions SET anomaly=?, score=?, reason=? WHERE id=?",
        [(int(a), float(s), rs, int(i)) for a, s, rs, i in zip(res["anomaly"], res["score"], res["reason"], res["id"])],
    )
    conn.commit()
    return int(res["anomaly"].sum())


def load_demo(conn: sqlite3.Connection, days: int = 90) -> dict:
    df = make_transactions(days=days, seed=int(datetime.now().strftime("%j")))
    return import_dataframe(conn, df[["ts", "description", "amount"]])


def reset(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM transactions")
    conn.commit()


def list_transactions(conn, category=None, anomalies_only=False, month=None, limit=500):
    sql, args = "SELECT * FROM transactions WHERE 1=1", []
    if category:
        sql += " AND category=?"; args.append(category)
    if anomalies_only:
        sql += " AND anomaly=1"
    if month:
        sql += " AND substr(ts,1,7)=?"; args.append(month)
    sql += " ORDER BY ts DESC LIMIT ?"; args.append(min(int(limit), 2000))
    return [dict(r) for r in conn.execute(sql, args).fetchall()]


def available_months(conn) -> list:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT substr(ts,1,7) m FROM transactions ORDER BY m DESC")]


def get_budgets(conn) -> dict:
    return {r["category"]: r["monthly_limit"] for r in conn.execute("SELECT * FROM budgets ORDER BY category")}


def set_budget(conn, category: str, limit: float) -> None:
    if limit < 0:
        raise ValueError("Budget cannot be negative")
    conn.execute("INSERT INTO budgets(category, monthly_limit) VALUES (?,?) "
                 "ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit", (category, limit))
    conn.commit()


def budget_status(spent: float, limit: float) -> str:
    if limit <= 0:
        return "ok" if spent == 0 else "exceeded"
    pct = spent / limit
    return "exceeded" if pct > 1 else "warning" if pct >= 0.8 else "ok"


def monthly_summary(conn, month: str | None = None) -> dict:
    months = available_months(conn)
    month = month or (months[0] if months else datetime.now().strftime("%Y-%m"))
    budgets = get_budgets(conn)
    spent = {r["category"]: r["t"] for r in conn.execute(
        "SELECT category, SUM(amount) t FROM transactions WHERE substr(ts,1,7)=? GROUP BY category", (month,))}
    cats = []
    for c in sorted(set(budgets) | set(spent)):
        s, lim = round(spent.get(c, 0.0), 2), budgets.get(c, 0.0)
        cats.append({"category": c, "spent": s, "limit": lim,
                     "percent": round(100 * s / lim, 1) if lim else None,
                     "status": budget_status(s, lim)})
    total = round(sum(spent.values()), 2)
    n_txn = conn.execute("SELECT COUNT(*) FROM transactions WHERE substr(ts,1,7)=?", (month,)).fetchone()[0]
    n_alert = conn.execute("SELECT COUNT(*) FROM transactions WHERE anomaly=1 AND substr(ts,1,7)=?", (month,)).fetchone()[0]
    trend = [{"month": r["m"], "total": round(r["t"], 2)} for r in conn.execute(
        "SELECT substr(ts,1,7) m, SUM(amount) t FROM transactions GROUP BY m ORDER BY m DESC LIMIT 6")][::-1]
    return {"month": month, "months": months, "total_spent": total, "transactions": n_txn,
            "fraud_alerts": n_alert, "categories": cats, "trend": trend,
            "budget_alerts": [
                f"{c['category']}: spent ₹{c['spent']:,.0f} of ₹{c['limit']:,.0f} ({c['percent']}%)"
                for c in cats if c["status"] != "ok"]}


def alerts(conn, month: str | None = None) -> list:
    return list_transactions(conn, anomalies_only=True, month=month, limit=200)
