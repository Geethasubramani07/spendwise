"""SpendWise FastAPI application.

Run:  uvicorn app.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__, service
from .categoriser import get_categoriser
from .db import get_conn
from .synthetic import CATEGORIES

STATIC = Path(__file__).parent / "static"
MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB

@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_categoriser()  # train once at start so the first request is fast
    yield


app = FastAPI(title="SpendWise", version=__version__, lifespan=lifespan,
              description="Expense tracker with ML categorisation and fraud alerts")


def db():
    conn = get_conn()
    try:
        yield conn
    finally:
        conn.close()


def require_admin(x_admin_token: str = Header(default="")):
    """Admin actions need the token from the ADMIN_TOKEN environment variable."""
    expected = os.environ.get("ADMIN_TOKEN", "admin123")
    if not secrets.compare_digest(x_admin_token, expected):
        raise HTTPException(status_code=403, detail="Admin token required")


class BudgetIn(BaseModel):
    monthly_limit: float = Field(ge=0, le=10_000_000)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": __version__}


@app.post("/api/transactions/import")
async def import_transactions(file: UploadFile = File(...), conn=Depends(db)):
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File too large (max 2 MB)")
    try:
        df = service.parse_csv(raw)
        return service.import_dataframe(conn, df, skipped=df.attrs.get("skipped", 0))
    except service.ImportError_ as exc:
        raise HTTPException(400, str(exc))


@app.post("/api/transactions/demo")
def load_demo(conn=Depends(db)):
    """Load synthetic demo data (no real financial data is ever needed)."""
    return service.load_demo(conn)


@app.get("/api/transactions")
def transactions(category: str | None = None, anomalies_only: bool = False,
                 month: str | None = None, limit: int = 500, conn=Depends(db)):
    return service.list_transactions(conn, category, anomalies_only, month, limit)


@app.get("/api/summary")
def summary(month: str | None = None, conn=Depends(db)):
    return service.monthly_summary(conn, month)


@app.get("/api/alerts")
def alerts(month: str | None = None, conn=Depends(db)):
    return service.alerts(conn, month)


@app.get("/api/budgets")
def budgets(conn=Depends(db)):
    return service.get_budgets(conn)


@app.put("/api/budgets/{category}")
def update_budget(category: str, body: BudgetIn, conn=Depends(db)):
    if category not in CATEGORIES + ["Other"]:
        raise HTTPException(404, "Unknown category")
    service.set_budget(conn, category, body.monthly_limit)
    return {"category": category, "monthly_limit": body.monthly_limit}


@app.post("/api/analyze", dependencies=[Depends(require_admin)])
def reanalyze(conn=Depends(db)):
    return {"alerts": service.run_detection(conn)}


@app.delete("/api/transactions", dependencies=[Depends(require_admin)])
def reset_data(conn=Depends(db)):
    service.reset(conn)
    return {"status": "cleared"}


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC / "index.html")
