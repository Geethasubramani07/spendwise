"""Anomaly detector (Isolation Forest) with human-readable reasons for every alert."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from .categoriser import normalize_merchant

MIN_HISTORY = 30  # below this the forest has too little data to be meaningful


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """df needs: ts (datetime), description, amount, category."""
    out = pd.DataFrame(index=df.index)
    merchant = df["description"].map(normalize_merchant)
    # typical spend per category; categories with < 5 rows fall back to the overall median
    cat_median = df.groupby("category")["amount"].transform("median")
    cat_size = df.groupby("category")["amount"].transform("size")
    medians = cat_median.where(cat_size >= 5, df["amount"].median()).clip(lower=1.0)
    out["log_amount"] = np.log1p(df["amount"])
    out["log_ratio"] = np.log(df["amount"] / medians)
    out["night"] = df["ts"].dt.hour.between(0, 5).astype(int)
    out["log_merchant_freq"] = np.log(merchant.map(merchant.value_counts()))
    # transactions within +/- 30 minutes (burst detector)
    # unit-safe seconds (pandas 3 uses microseconds, older versions nanoseconds)
    secs = (df["ts"] - pd.Timestamp("1970-01-01")) / pd.Timedelta(seconds=1)
    secs = secs.to_numpy(dtype=float)
    arr = np.sort(secs)
    lo = np.searchsorted(arr, secs - 1800, side="left")
    hi = np.searchsorted(arr, secs + 1800, side="right")
    out["burst"] = (hi - lo).astype(float)
    out["_ratio"] = df["amount"] / medians
    out["_merchant_freq"] = merchant.map(merchant.value_counts())
    return out


MODEL_COLS = ["log_amount", "log_ratio", "night", "log_merchant_freq", "burst"]


def _reasons(row, ts, category) -> str:
    parts = []
    if row["_ratio"] >= 4:
        parts.append(f"Amount is {row['_ratio']:.1f}x your typical {category} spend")
    if row["night"] == 1:
        parts.append(f"Made at {ts.strftime('%H:%M')} (night-time)")
    if row["_merchant_freq"] <= 2:
        parts.append("Rare or first-time merchant")
    if row["burst"] >= 4:
        parts.append(f"{int(row['burst'])} transactions within one hour")
    return "; ".join(parts) or "Unusual combination of amount, time and merchant"


def detect(df: pd.DataFrame, contamination: float = 0.05, seed: int = 42) -> pd.DataFrame:
    """Return df copy with columns: anomaly (bool), score (higher = more suspicious), reason."""
    df = df.copy()
    df["ts"] = pd.to_datetime(df["ts"])
    df = df.reset_index(drop=True)
    if df.empty:
        df["anomaly"], df["score"], df["reason"] = [], [], []
        return df
    feats = build_features(df)
    if len(df) < MIN_HISTORY:
        df["anomaly"] = feats["_ratio"] >= 6
        df["score"] = feats["_ratio"].clip(upper=10) / 10
    else:
        X = feats[MODEL_COLS].to_numpy()
        forest = IsolationForest(n_estimators=200, contamination=contamination, random_state=seed)
        forest.fit(X)
        df["anomaly"] = forest.predict(X) == -1
        df["score"] = -forest.score_samples(X)
    df["reason"] = [
        _reasons(feats.loc[i], df.loc[i, "ts"], df.loc[i, "category"]) if df.loc[i, "anomaly"] else ""
        for i in df.index
    ]
    return df
