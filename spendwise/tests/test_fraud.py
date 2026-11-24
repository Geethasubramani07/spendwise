from app.categoriser import get_categoriser
from app.fraud import detect
from app.synthetic import make_transactions


def _prepared(seed):
    df = make_transactions(days=180, seed=seed)
    df["category"] = get_categoriser().predict_many(df["description"].tolist())
    return df


def test_recall_meets_target_on_average():
    recalls = []
    for seed in (1, 2, 3, 4, 5):
        df = _prepared(seed)
        res = detect(df)
        tp = (res["anomaly"] & df["is_injected"]).sum()
        recalls.append(tp / df["is_injected"].sum())
    assert sum(recalls) / len(recalls) >= 0.70


def test_every_alert_has_a_reason():
    res = detect(_prepared(3))
    flagged = res[res["anomaly"]]
    assert len(flagged) > 0
    assert (flagged["reason"].str.len() > 0).all()
    assert (res.loc[~res["anomaly"], "reason"] == "").all()


def test_small_history_uses_rule_fallback():
    df = _prepared(1).head(10).copy()
    df.loc[df.index[0], "amount"] = df["amount"].median() * 50
    res = detect(df)
    assert res["anomaly"].sum() >= 1


def test_empty_frame():
    import pandas as pd
    res = detect(pd.DataFrame(columns=["ts", "description", "amount", "category"]))
    assert len(res) == 0
