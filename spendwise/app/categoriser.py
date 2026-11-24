"""Transaction categoriser: keyword rules first, then a TF-IDF + Logistic Regression model."""
from __future__ import annotations

import re
import threading

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

from .synthetic import make_training_set

RULES = {
    "Food": ["swiggy", "zomato", "pizza", "restaurant", "cafe", "coffee", "grocery", "bakery", "biryani"],
    "Transport": ["uber", "ola ", "fuel", "petrol", "metro", "taxi", "irctc", "rapido", "bus pass"],
    "Shopping": ["amazon", "flipkart", "myntra", "mall", "store", "shop"],
    "Bills": ["recharge", "electricity", "broadband", "internet bill", "gas cylinder", "water board"],
    "Entertainment": ["netflix", "spotify", "bookmyshow", "cinema", "hotstar", "gaming"],
    "Health": ["pharmacy", "hospital", "clinic", "medicine", "practo", "dental"],
    "Education": ["udemy", "coursera", "tuition", "college fee", "course fee", "unacademy"],
}

_PREFIX = re.compile(r"\b(upi|pos|neft|imps|card purchase|payment|order)\b", re.I)


def normalize_merchant(description: str) -> str:
    """Reduce a bank narration to a stable merchant key (lowercase words, no digits)."""
    text = description.lower()
    text = _PREFIX.sub(" ", text)
    text = re.sub(r"[\d#/\-_.]+", " ", text)
    text = re.sub(r"\bbengaluru\b", " ", text)
    words = [w for w in re.split(r"\s+", text) if w]
    return " ".join(words[:3]) or "unknown"


class Categoriser:
    def __init__(self, min_confidence: float = 0.35):
        self.min_confidence = min_confidence
        texts, labels = make_training_set()
        self.model = make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4), lowercase=True),
            LogisticRegression(max_iter=1000, C=10.0),
        )
        self.model.fit([normalize_merchant(t) for t in texts], labels)

    def rule_predict(self, description: str):
        low = " " + description.lower() + " "
        for cat, words in RULES.items():
            if any(w in low for w in words):
                return cat
        return None

    def predict(self, description: str) -> str:
        cat = self.rule_predict(description)
        if cat:
            return cat
        key = normalize_merchant(description)
        proba = self.model.predict_proba([key])[0]
        best = proba.argmax()
        if proba[best] < self.min_confidence:
            return "Other"
        return str(self.model.classes_[best])

    def predict_many(self, descriptions):
        return [self.predict(d) for d in descriptions]


_instance = None
_lock = threading.Lock()


def get_categoriser() -> Categoriser:
    global _instance
    with _lock:
        if _instance is None:
            _instance = Categoriser()
        return _instance
