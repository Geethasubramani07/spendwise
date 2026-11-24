"""Measure the handbook's success metrics on synthetic data.

Run:  python scripts/evaluate.py
Targets: categorisation accuracy >= 85%, fraud recall >= 70% on injected anomalies.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.categoriser import get_categoriser  # noqa: E402
from app.fraud import detect  # noqa: E402
from app.synthetic import make_category_test_set, make_transactions  # noqa: E402


def categorisation_accuracy() -> float:
    texts, labels = make_category_test_set()
    preds = get_categoriser().predict_many(texts)
    return sum(p == y for p, y in zip(preds, labels)) / len(labels)


def fraud_metrics(seeds=(1, 2, 3, 4, 5)) -> dict:
    cat = get_categoriser()
    recalls, precisions = [], []
    for s in seeds:
        df = make_transactions(days=180, seed=s)
        df["category"] = cat.predict_many(df["description"].tolist())
        res = detect(df)
        tp = int((res["anomaly"] & df["is_injected"]).sum())
        fn = int((~res["anomaly"] & df["is_injected"]).sum())
        fp = int((res["anomaly"] & ~df["is_injected"]).sum())
        recalls.append(tp / (tp + fn))
        precisions.append(tp / (tp + fp) if tp + fp else 0.0)
    return {"recall": sum(recalls) / len(recalls), "precision": sum(precisions) / len(precisions),
            "runs": len(seeds), "recall_per_run": [round(r, 3) for r in recalls]}


if __name__ == "__main__":
    acc = categorisation_accuracy()
    fr = fraud_metrics()
    out = {
        "categorisation_accuracy": round(acc, 3), "categorisation_target": 0.85,
        "fraud_recall": round(fr["recall"], 3), "fraud_recall_target": 0.70,
        "fraud_precision": round(fr["precision"], 3), "fraud_runs": fr["runs"],
        "fraud_recall_per_run": fr["recall_per_run"],
        "note": "Synthetic data with injected anomalies; real-world results will differ.",
    }
    print(json.dumps(out, indent=2))
    Path(__file__).resolve().parent.parent.joinpath("docs", "RESULTS.json").write_text(json.dumps(out, indent=2))
