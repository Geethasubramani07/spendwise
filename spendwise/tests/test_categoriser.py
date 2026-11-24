from app.categoriser import get_categoriser, normalize_merchant
from app.synthetic import make_category_test_set


def test_normalize_merchant_strips_noise():
    assert normalize_merchant("UPI/Swiggy/123456") == "swiggy"
    assert normalize_merchant("POS Amazon BENGALURU") == "amazon"


def test_known_merchants():
    c = get_categoriser()
    assert c.predict("UPI/Swiggy/445566") == "Food"
    assert c.predict("Uber trip 1234") == "Transport"
    assert c.predict("NETFLIX PAYMENT 998877") == "Entertainment"


def test_unseen_merchant_uses_model_or_rules():
    assert get_categoriser().predict("City Hospital 4455") == "Health"


def test_gibberish_goes_to_other_or_valid_category():
    assert get_categoriser().predict("XQZV 9981") in {"Other", "Food", "Transport", "Shopping",
                                                       "Bills", "Entertainment", "Health", "Education"}


def test_accuracy_meets_target():
    texts, labels = make_category_test_set()
    preds = get_categoriser().predict_many(texts)
    acc = sum(p == y for p, y in zip(preds, labels)) / len(labels)
    assert acc >= 0.85, f"accuracy {acc:.3f} below 85% target"
