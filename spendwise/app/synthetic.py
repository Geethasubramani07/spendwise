"""Synthetic data only (the handbook says financial data is sensitive).

Used for: demo data, categoriser training, and the evaluation script.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills",
    "Entertainment", "Health", "Education",
]

MERCHANTS = {
    "Food": ["Swiggy", "Zomato", "Dominos Pizza", "Starbucks", "McDonalds",
             "Cafe Coffee Day", "Big Basket", "Dmart Grocery", "Burger King", "Haldirams"],
    "Transport": ["Uber", "Ola Cabs", "Indian Oil Fuel", "Metro Recharge",
                  "Rapido", "IRCTC Train", "Shell Petrol Pump"],
    "Shopping": ["Amazon", "Flipkart", "Myntra", "Zara", "Reliance Trends",
                 "Decathlon", "Croma Electronics"],
    "Bills": ["Airtel Recharge", "Jio Fiber", "BESCOM Electricity", "Tata Power",
              "Water Board", "Broadband Bill", "Gas Cylinder Booking"],
    "Entertainment": ["Netflix", "Spotify", "BookMyShow", "PVR Cinemas",
                      "Steam Games", "Hotstar"],
    "Health": ["Apollo Pharmacy", "Practo Consult", "1mg Medicines", "Cult Fit", "Lenskart"],
    "Education": ["Udemy", "Coursera", "Byjus", "College Fee", "Unacademy", "Stationery Mart"],
}

# Merchants never used for training: only for honest held-out testing.
UNSEEN_MERCHANTS = {
    "Food": ["Pizza Hut Outlet", "Local Bakery", "Fresh Mart Vegetables", "Biryani House"],
    "Transport": ["City Taxi Service", "Bus Pass Office", "Petrol Bunk Express"],
    "Shopping": ["Westside Store", "Lifestyle Mall", "Online Gadget Shop"],
    "Bills": ["Electricity Board Payment", "Mobile Recharge Plan", "Internet Bill Pay"],
    "Entertainment": ["Cinema Hall Tickets", "Music Streaming Plan", "Gaming Store"],
    "Health": ["City Hospital", "Dental Clinic", "Medical Store"],
    "Education": ["Online Course Fee", "Tuition Centre", "Book Store Campus"],
}

# (median INR, spread) per category for log-normal amounts
AMOUNT_PROFILE = {
    "Food": (350, 0.6), "Transport": (220, 0.6), "Shopping": (1800, 0.7),
    "Bills": (900, 0.5), "Entertainment": (400, 0.5), "Health": (600, 0.7),
    "Education": (1500, 0.6),
}

TEMPLATES = [
    "UPI/{m}/{ref}", "POS {m} BENGALURU", "{m} ORDER #{n}",
    "{M} PAYMENT {ref}", "NEFT-{m}-{ref}", "{m}", "CARD PURCHASE {M} {n}",
]


def _narration(rng: random.Random, merchant: str) -> str:
    t = rng.choice(TEMPLATES)
    return t.format(m=merchant, M=merchant.upper(),
                    ref=rng.randint(100000, 999999), n=rng.randint(1000, 9999))


def make_training_set(n: int = 1400, seed: int = 1):
    rng = random.Random(seed)
    texts, labels = [], []
    for _ in range(n):
        cat = rng.choice(CATEGORIES)
        texts.append(_narration(rng, rng.choice(MERCHANTS[cat])))
        labels.append(cat)
    return texts, labels


def make_category_test_set(n: int = 600, seed: int = 99, unseen_share: float = 0.3):
    """Held-out set: different seed, and some merchants the model never saw."""
    rng = random.Random(seed)
    texts, labels = [], []
    for _ in range(n):
        cat = rng.choice(CATEGORIES)
        pool = UNSEEN_MERCHANTS[cat] if rng.random() < unseen_share else MERCHANTS[cat]
        texts.append(_narration(rng, rng.choice(pool)))
        labels.append(cat)
    return texts, labels


def _normal_ts(rng: random.Random, start: datetime, days: int) -> datetime:
    day = start + timedelta(days=rng.randrange(days))
    hour = rng.choices(range(24), weights=[0, 0, 0, 0, 0, 1, 2, 4, 6, 6, 5, 6, 8,
                                           7, 5, 5, 6, 7, 8, 9, 8, 6, 3, 1])[0]
    return day.replace(hour=hour, minute=rng.randrange(60), second=rng.randrange(60))


def make_transactions(days: int = 180, per_day: float = 3.5, inject_rate: float = 0.03,
                      seed: int = 7, end: datetime | None = None) -> pd.DataFrame:
    """Normal spending plus injected anomalies (is_injected=True)."""
    rng = random.Random(seed)
    nprng = np.random.default_rng(seed)
    end = end or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=days)
    n_normal = int(days * per_day)
    rows = []
    for _ in range(n_normal):
        cat = rng.choice(CATEGORIES)
        med, sigma = AMOUNT_PROFILE[cat]
        amt = round(float(nprng.lognormal(np.log(med), sigma)), 2)
        rows.append((_normal_ts(rng, start, days), _narration(rng, rng.choice(MERCHANTS[cat])),
                     amt, cat, False))

    n_inject = max(1, int(n_normal * inject_rate))
    injected = 0
    while injected < n_inject:
        kind = rng.choice(["big", "night", "burst", "intl"])
        if kind == "big":
            cat = rng.choice(CATEGORIES)
            med, _ = AMOUNT_PROFILE[cat]
            rows.append((_normal_ts(rng, start, days),
                         _narration(rng, rng.choice(MERCHANTS[cat])),
                         round(med * rng.uniform(9, 25), 2), cat, True))
            injected += 1
        elif kind == "night":
            day = start + timedelta(days=rng.randrange(days))
            ts = day.replace(hour=rng.randint(1, 4), minute=rng.randrange(60))
            rows.append((ts, f"UPI/QUICKCASH EXCH {rng.randint(1000, 9999)}/{rng.randint(100000, 999999)}",
                         round(rng.uniform(8000, 40000), 2), "Shopping", True))
            injected += 1
        elif kind == "intl":
            rows.append((_normal_ts(rng, start, days),
                         f"INTL WIRE TRF {rng.choice(['LAGOS', 'MINSK', 'DUBAI'])} {rng.randint(1000, 9999)}",
                         round(rng.uniform(15000, 60000), 2), "Shopping", True))
            injected += 1
        else:  # burst of rapid small-to-mid charges at one odd merchant
            day = start + timedelta(days=rng.randrange(days))
            base = day.replace(hour=rng.randint(10, 22), minute=rng.randrange(40))
            shop = f"GIFTCARD HUB {rng.randint(100, 999)}"
            for k in range(rng.randint(5, 7)):
                rows.append((base + timedelta(minutes=2 * k), f"POS {shop} {rng.randint(1000, 9999)}",
                             round(rng.uniform(2500, 5000), 2), "Shopping", True))
                injected += 1

    df = pd.DataFrame(rows, columns=["ts", "description", "amount", "category_true", "is_injected"])
    return df.sort_values("ts").reset_index(drop=True)
