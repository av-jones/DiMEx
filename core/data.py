"""Data loading, batch scoring and per-drug summaries.

FAKE DATA: the generators below make illustrative reviews so the app runs
before training is done. Replace them with:
  - predictions.parquet: batch-scored Drugs.com reviews (see scripts/batch_score.py)
  - Druglib's real test split for the model check page
"""
import math
import random
from pathlib import Path

import pandas as pd

from core.labels import typical_severity, va_to_rating
from core.registry import MODEL_NAMES, Predictor

PRED_PATH = Path(__file__).resolve().parent.parent / "data" / "predictions.parquet"

# ---------------- Drugs.com side (main pages) ----------------

_EFFECT = [("It finally stopped my panic attacks.", 9), ("My mood lifted after a few weeks.", 8),
           ("It took the edge off but I still struggle some days.", 6),
           ("No change at all after two months.", 2)]
_SIDE = ["Some mild nausea the first week, then it faded.",
         "I was wide awake until 3am most nights.",
         "I feel nothing at all, completely numb.",
         "Severe headache every afternoon.",
         "Exhausted all day, I could barely work.",
         "Gained about ten pounds.",
         "A little dizzy when I stand up.",
         "My sex drive is gone and it is awful."]
_DRUGS = {"Sertraline": ["Anxiety", "Depression"], "Escitalopram": ["Anxiety", "Depression"],
          "Bupropion": ["Depression", "Smoking cessation"]}


def fake_reviews(per_group=40, seed=7):
    rng = random.Random(seed)
    rows, rid = [], 1000
    for drug, conditions in _DRUGS.items():
        for cond in conditions:
            for _ in range(per_group):
                eff, base = rng.choice(_EFFECT)
                sides = rng.sample(_SIDE, rng.choice([0, 1, 1, 2]))
                rating = max(1, min(10, base + rng.choice([-1, 0, 0, 1])))
                rows.append({"review_id": rid, "drug": drug, "condition": cond,
                             "rating": rating, "text": " ".join([eff] + sides)})
                rid += 1
    return pd.DataFrame(rows)


def batch_score(reviews, model_names=MODEL_NAMES):
    """Score every review with every model. One row per (review, model, aspect)."""
    rows = []
    for name in model_names:
        predictor = Predictor(name)
        for r in reviews.itertuples():
            for item in predictor.predict(r.text):
                rows.append({"review_id": r.review_id, "drug": r.drug, "condition": r.condition,
                             "rating": r.rating, "text": r.text, "model": name, **item})
    return pd.DataFrame(rows)


def load_predictions():
    if PRED_PATH.exists():
        return pd.read_parquet(PRED_PATH)
    return batch_score(fake_reviews())


def summarize(df, drug, condition, model):
    sub = df[(df.drug == drug) & (df.condition == condition) & (df.model == model)]
    n = sub.review_id.nunique()
    if n == 0:
        return None
    eff = sub[sub.kind == "effectiveness"].label.value_counts(normalize=True)
    side = sub[sub.kind == "side_effect"]
    effects = [{"name": name, "share": g.review_id.nunique() / n,
                "severity": typical_severity(g.label)}
               for name, g in side.groupby("aspect")]
    effects.sort(key=lambda e: e["share"], reverse=True)

    severe_ids = set(side[side.label == "Severe"].review_id)
    ratings = sub.drop_duplicates("review_id").set_index("review_id").rating
    mismatch = int(sum(1 for rid in severe_ids if ratings[rid] >= 9))

    quotes, used = [], set()
    for _, row in side.sort_values("label", key=lambda s: s.map({"Severe": 0, "Moderate": 1, "Mild": 2})).iterrows():
        if row.aspect not in used:
            quotes.append(row)
            used.add(row.aspect)
        if len(quotes) == 3:
            break
    return {"n": n, "worked": eff.get("Worked well", 0.0), "some": eff.get("Some benefit", 0.0),
            "none": eff.get("Didn't help", 0.0), "effects": effects, "mismatch": mismatch,
            "quotes": quotes}


# ---------------- Druglib side (model check page) ----------------
# Each review has three text fields and the patient's own ratings:
# effectiveness 1-5, side effects 1-5 (5 = extremely severe), satisfaction 1-10.

FIELDS = [("benefits", "Benefits", "Effectiveness", "effectiveness", 5),
          ("side_effects", "Side effects", "Side-effect severity", "side_effect", 5),
          ("comment", "Overall comment", "Satisfaction", "satisfaction", 10)]

_DRUGLIB_TEST = [
    {"id": "#0412", "drug": "Zoloft", "condition": "depression", "ratings": [4, 3, 7],
     "benefits": "My mood lifted after about five weeks. I could focus at work again.",
     "side_effects": "Some nausea and headaches the first two weeks, and it is harder to sleep through the night.",
     "comment": "Took 50mg every morning. Overall it helped a lot, but the sleep issue still bothers me."},
    {"id": "#0877", "drug": "Lexapro", "condition": "anxiety", "ratings": [3, 4, 3],
     "benefits": "Took the edge off my anxiety but I still had panic attacks at work.",
     "side_effects": "Felt exhausted all day and gained about ten pounds.",
     "comment": "Stopped after four months. Not worth the weight gain for me."},
    {"id": "#0931", "drug": "Lexapro", "condition": "depression", "ratings": [5, 1, 9],
     "benefits": "Works great, I finally feel like myself again.",
     "side_effects": "None that I noticed.",
     "comment": "Best medication I have tried. It helped right away."},
    {"id": "#1002", "drug": "Zoloft", "condition": "OCD", "ratings": [2, 4, 2],
     "benefits": "No change in my intrusive thoughts after three months.",
     "side_effects": "Severe insomnia and I felt terrible most days.",
     "comment": "Didn't help and the side effects were awful."},
]


def druglib_test():
    return _DRUGLIB_TEST


def druglib_scores(predictor, review):
    """Model scores on Druglib's rating scales for one review: list of 3 floats."""
    out = []
    for key, _, aspect, kind, scale in FIELDS:
        va_kind = "side_effect" if kind == "side_effect" else "effectiveness"
        v, _ = predictor.score_field(review[key], aspect, va_kind)
        out.append(round(min(scale, max(1, va_to_rating(v, kind))), 1))
    return out


def evaluate(model_names=MODEL_NAMES):
    """RMSE and MAE per model and aspect on the test split."""
    rows = []
    for name in model_names:
        p = Predictor(name)
        errs = [[], [], []]
        for r in druglib_test():
            for i, s in enumerate(druglib_scores(p, r)):
                errs[i].append(s - r["ratings"][i])
        row = {"Model": name}
        for (_, _, label, _, _), e in zip(FIELDS, errs):
            row[f"{label} RMSE"] = round(math.sqrt(sum(x * x for x in e) / len(e)), 2)
            row[f"{label} MAE"] = round(sum(abs(x) for x in e) / len(e), 2)
        rows.append(row)
    return pd.DataFrame(rows)
