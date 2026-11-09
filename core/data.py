"""Data loading, batch scoring and per-drug summaries.

FAKE DATA: the generators below make illustrative reviews so the app runs
before training is done. Replace them with:
  - predictions.parquet: batch-scored Drugs.com reviews (see scripts/batch_score.py)
  - Druglib's real test split for the model check page
"""
import math
import random
import zlib
from pathlib import Path

import pandas as pd

from core.explain import intensity_band
from core.labels import rating_label, typical_severity, va_to_rating
from core.registry import APP_MODEL, MODEL_NAMES, Predictor

SIDE_EFFECT_PRESENT = 1.6   # whole-review side-effect score (1-5) at which side effects count as reported
PRED_PATH = Path(__file__).resolve().parent.parent / "data" / "predictions.parquet"
# Drugs.com drug-condition pairs with review counts (names and counts only; scripts/export_pairs.py)
PAIRS_PATH = Path(__file__).resolve().parent.parent / "assets" / "drugscom_pairs.csv"
PLACEHOLDER_CAP = 150   # placeholder reviews generated per pair (enough for every chart, quick to score)

# ---------------- Drugs.com side (main pages) ----------------

# Effectiveness sentences, filled with the condition's main symptom, and the star rating they suggest
_EFFECT = [("It finally got my {s} under control.", 9), ("My {s} improved after a few weeks.", 8),
           ("It helped my {s} a little, but not enough.", 6),
           ("No change in my {s} at all after two months.", 2)]
_SYMPTOM = {
    "Anxiety": "anxiety", "Depression": "depression", "Smoking cessation": "cravings",
    "Type 2 diabetes": "blood sugar", "Weight loss": "weight", "High blood pressure": "blood pressure",
    "High cholesterol": "cholesterol", "Migraine": "migraines", "Epilepsy": "seizures",
    "Insomnia": "sleep", "ADHD": "focus", "Bipolar disorder": "mood swings",
    "Schizophrenia": "symptoms", "Acne": "acne", "Psoriasis": "skin",
    "Rheumatoid arthritis": "joint pain", "Osteoarthritis": "knee pain", "Asthma": "breathing",
    "COPD": "breathing", "Allergies": "allergies", "GERD": "heartburn",
    "Hypothyroidism": "thyroid levels", "Neuropathic pain": "nerve pain",
    "Restless legs syndrome": "restless legs", "Fibromyalgia": "pain",
    "Overactive bladder": "bladder control", "Erectile dysfunction": "symptoms",
    "Birth control": "cycle", "Chronic pain": "pain", "Panic disorder": "panic attacks",
    "OCD": "intrusive thoughts", "Atrial fibrillation": "heart rhythm",
    "Urinary tract infection": "infection",
}
_SYMPTOM_LOWER = {**{k.lower(): v for k, v in _SYMPTOM.items()},
                  "birth control": "cycle", "pain": "pain", "weight loss": "weight", "obesity": "weight",
                  "bipolar disorder": "mood swings", "smoking cessation": "cravings",
                  "high blood pressure": "blood pressure", "emergency contraception": "worry",
                  "vaginal yeast infection": "infection", "constipation": "constipation",
                  "diabetes, type 2": "blood sugar", "opiate dependence": "cravings",
                  "major depressive disorder": "depression", "generalized anxiety disorder": "anxiety",
                  "rosacea": "redness", "muscle spasm": "spasms", "irritable bowel syndrome": "stomach",
                  "hyperhidrosis": "sweating", "cough": "cough", "nausea/vomiting": "nausea",
                  "back pain": "back pain", "headache": "headaches", "sinusitis": "sinuses"}
_SIDE = ["Some mild nausea the first week, then it faded.",
         "I was wide awake until 3am most nights.",
         "I feel nothing at all, completely numb.",
         "Severe headache every afternoon.",
         "Exhausted all day, I could barely work.",
         "Gained about ten pounds.",
         "A little dizzy when I stand up.",
         "My sex drive is gone and it is awful."]
# Placeholder drugs, each with conditions it is commonly prescribed for
_DRUGS = {
    "Sertraline": ["Anxiety", "Depression"], "Escitalopram": ["Anxiety", "Depression"],
    "Bupropion": ["Depression", "Smoking cessation"],
    "Metformin": ["Type 2 diabetes"], "Semaglutide": ["Type 2 diabetes", "Weight loss"],
    "Lisinopril": ["High blood pressure"], "Atorvastatin": ["High cholesterol"],
    "Sumatriptan": ["Migraine"], "Topiramate": ["Migraine", "Epilepsy"],
    "Zolpidem": ["Insomnia"], "Trazodone": ["Insomnia", "Depression"],
    "Methylphenidate": ["ADHD"], "Lamotrigine": ["Bipolar disorder", "Epilepsy"],
    "Quetiapine": ["Bipolar disorder", "Schizophrenia"], "Isotretinoin": ["Acne"],
    "Adalimumab": ["Psoriasis", "Rheumatoid arthritis"], "Methotrexate": ["Rheumatoid arthritis"],
    "Celecoxib": ["Osteoarthritis"], "Albuterol": ["Asthma", "COPD"],
    "Montelukast": ["Asthma", "Allergies"], "Cetirizine": ["Allergies"], "Omeprazole": ["GERD"],
    "Levothyroxine": ["Hypothyroidism"], "Gabapentin": ["Neuropathic pain", "Restless legs syndrome"],
    "Duloxetine": ["Fibromyalgia", "Depression"], "Oxybutynin": ["Overactive bladder"],
    "Sildenafil": ["Erectile dysfunction"], "Levonorgestrel": ["Birth control"],
    "Tramadol": ["Chronic pain"], "Clonazepam": ["Panic disorder"],
    "Fluoxetine": ["OCD", "Depression"], "Apixaban": ["Atrial fibrillation"],
    "Nitrofurantoin": ["Urinary tract infection"],
}


def fake_reviews(per_group=25, seed=7):
    rng = random.Random(seed)
    rows, rid = [], 1000
    for drug, conditions in _DRUGS.items():
        for cond in conditions:
            for _ in range(rng.randint(per_group // 2, per_group * 4)):   # uneven, like real data
                eff, base = rng.choice(_EFFECT)
                eff = eff.format(s=_SYMPTOM[cond])
                sides = rng.sample(_SIDE, rng.choice([0, 1, 1, 2]))
                rating = max(1, min(10, base + rng.choice([-1, 0, 0, 1])))
                rows.append({"review_id": rid, "drug": drug, "condition": cond,
                             "rating": rating, "text": " ".join([eff] + sides)})
                rid += 1
    return pd.DataFrame(rows)


MIN_REVIEWS = 10   # drug-condition pairs with fewer reviews are too thin to summarize (keeps ~92% of Drugs.com)

# Drugs.com condition names were damaged when the dataset was scraped: some lost a trailing "r"
# ("Bipolar Disorde"), some lost leading letters ("ibromyalgia"), some are drug-name fragments
# ("min / sitagliptin)") or page text ("3</span> users found this comment helpful.").
_ADD_R = ("Disorde", "Bladde", "Othe", "Cance", "Ulce", "Zoste", "Flutte", "Shoulde", "Feve")
_FRONT = {"ibromyalgia": "Fibromyalgia", "mance Anxiety": "Performance Anxiety", "emale ": "Female ",
          "atigue": "Fatigue", "acial ": "Facial ", "zen Shoulde": "Frozen Shoulde", "amilial ": "Familial ",
          "lic Acid": "Folic Acid", "cal Segmental": "Focal Segmental", "actor IX": "Factor IX",
          "llicle ": "Follicle ", "llicular ": "Follicular ", "ailure ": "Failure ", "unctional ": "Functional ",
          "ungal ": "Fungal ", "ibrocystic ": "Fibrocystic "}
_DROP = {"Not Listed / Other"}


def clean_condition(name):
    """Repaired condition name, or None for entries that aren't a condition."""
    if not isinstance(name, str) or "</span>" in name:
        return None
    name = " ".join(name.split())
    for broken, fixed in _FRONT.items():
        if name.startswith(broken):
            name = fixed + name[len(broken):]
            break
    words = name.split(" ")
    words = [w + "r" if w.endswith(_ADD_R) or w.split("/")[-1] in _ADD_R else w for w in words]
    name = " ".join(words)
    if name in _DROP or (name[:1].islower() and not name.startswith("von ")):
        return None                       # unrepairable fragments
    return name


def pair_counts(df, min_reviews=MIN_REVIEWS):
    """Reviews per drug-condition pair, keeping pairs with at least min_reviews."""
    n = df.groupby(["drug", "condition"]).review_id.nunique().rename("n").reset_index()
    return n[n.n >= min_reviews].sort_values("n", ascending=False, ignore_index=True)


def batch_score(reviews, model_names=MODEL_NAMES):
    """Score every review with every model. Two kinds of rows per (review, model):
    scope "review": the three trained aspects scored on the whole review (score = Druglib scale);
    scope "mention": side effects found by keyword, each scored on its own (experimental)."""
    rows = []
    for name in model_names:
        predictor = Predictor(name)
        for r in reviews.itertuples():
            base = {"review_id": r.review_id, "drug": r.drug, "condition": r.condition,
                    "rating": r.rating, "text": r.text, "model": name}
            for item in predictor.score_review(r.text):
                rows.append({**base, "scope": "review", "aspect": item["aspect"], "kind": item["kind"],
                             "span": None, "valence": item["valence"], "arousal": item["arousal"],
                             "label": item["label"], "score": item["rating"], "scale": item["scale"]})
            for item in predictor.predict(r.text):
                rows.append({**base, "scope": "mention", **item})
    return pd.DataFrame(rows)


def fake_pair_reviews(drug, condition, n):
    """Placeholder reviews for any drug-condition pair. Seeded by the pair, so the same pair always gets
    the same reviews, and each pair gets its own mix of good and bad outcomes."""
    seed = zlib.crc32(f"{drug}|{condition}".encode())
    rng = random.Random(seed)
    symptom = _SYMPTOM_LOWER.get(condition.lower(), "symptoms")
    outcome_w = [rng.random() + 0.2 for _ in _EFFECT]            # this pair's lean
    side_k = rng.choice([[0, 0, 1], [0, 1, 1, 2], [1, 1, 2, 2]])  # how many side effects people mention
    rows = []
    for i in range(n):
        eff, base = rng.choices(_EFFECT, weights=outcome_w)[0]
        sides = rng.sample(_SIDE, rng.choice(side_k))
        rating = max(1, min(10, base + rng.choice([-1, 0, 0, 1])))
        rows.append({"review_id": (seed % 100_000) * 1000 + i, "drug": drug, "condition": condition,
                     "rating": rating, "text": " ".join([eff.format(s=symptom)] + sides)})
    return pd.DataFrame(rows)


def load_pairs():
    """Drug-condition pairs with review counts, most reviewed first.
    Real predictions if they exist; else the real Drugs.com names and counts (assets/drugscom_pairs.csv);
    else the small built-in placeholder set."""
    if PRED_PATH.exists():
        return pair_counts(load_predictions())
    if PAIRS_PATH.exists():
        return pd.read_csv(PAIRS_PATH)
    return pair_counts(fake_reviews())


def pair_predictions(drug, condition):
    """Predictions for one drug-condition pair: real ones if they exist, else placeholder reviews scored now."""
    if PRED_PATH.exists():
        df = load_predictions()
        return df[(df.drug == drug) & (df.condition == condition)]
    pairs = load_pairs()
    n = pairs[(pairs.drug == drug) & (pairs.condition == condition)].n
    return batch_score(fake_pair_reviews(drug, condition, min(int(n.iloc[0]) if len(n) else 25, PLACEHOLDER_CAP)),
                       [APP_MODEL])


def load_predictions():
    """Predictions from the app's model: data/predictions.parquet if it exists, else placeholders."""
    if PRED_PATH.exists():
        df = pd.read_parquet(PRED_PATH)
        return df[df.model == APP_MODEL] if APP_MODEL in set(df.model) else df
    return batch_score(fake_reviews(), [APP_MODEL])


# Levels for each aspect's breakdown, best first (side effects: none first)
BREAKDOWN_LEVELS = {
    "effectiveness": ["Highly effective", "Considerably effective", "Moderately effective",
                      "Marginally effective", "Ineffective"],
    "side_effect": ["No side effects", "Mild side effects", "Moderate side effects",
                    "Severe side effects", "Extremely severe side effects"],
    "satisfaction": ["Satisfied", "Mixed", "Dissatisfied"],
}
SPLIT_SHARE = 0.30     # both ends this common -> reviews disagree


def _is_split(kind, levels):
    """True when reviews cluster at both ends, so the average hides a disagreement."""
    names = BREAKDOWN_LEVELS[kind]
    top, bottom = (names[:2], names[-2:]) if kind != "satisfaction" else (names[:1], names[-1:])
    return (sum(levels.get(n, 0) for n in top) >= SPLIT_SHARE
            and sum(levels.get(n, 0) for n in bottom) >= SPLIT_SHARE)


def _bands(arousal):
    bands = pd.Series([intensity_band(a, "side_effect") for a in arousal], dtype=object)
    shares = bands.value_counts(normalize=True)
    return {b: float(shares.get(b, 0.0)) for b in ("Mild", "Moderate", "Distressing")}


def mentions(df):
    """Rows for keyword-found side effects (older prediction files have no scope column)."""
    return df[df.scope == "mention"] if "scope" in df else df


def summarize(df, drug, condition, model):
    """Everything the drug page shows for one drug, condition and model."""
    sub = df[(df.drug == drug) & (df.condition == condition) & (df.model == model)]
    n = sub.review_id.nunique()
    if n == 0:
        return None
    whole = sub[sub.scope == "review"] if "scope" in sub else sub.iloc[0:0]
    ment = mentions(sub)
    side_m = ment[ment.kind == "side_effect"]

    tiles = {}
    for kind in ("effectiveness", "side_effect", "satisfaction"):
        g = whole[whole.kind == kind]
        if len(g):
            mean = float(g.score.mean())
            levels = pd.Series([rating_label(kind, x) for x in g.score]).value_counts(normalize=True)
            breakdown = [(name, float(levels.get(name, 0.0))) for name in BREAKDOWN_LEVELS[kind]]
            tiles[kind] = {"mean": mean, "scale": int(g.scale.iloc[0]), "label": rating_label(kind, mean),
                           "breakdown": breakdown, "split": _is_split(kind, levels)}

    # Side-effect intensity: reviews whose whole-review side-effect score shows any side effects
    side_w = whole[(whole.kind == "side_effect") & (whole.score >= SIDE_EFFECT_PRESENT)]
    intensity = _bands(side_w.arousal) if len(side_w) else None
    dots = pd.DataFrame({"v": side_w.valence, "a": side_w.arousal,
                         "band": [intensity_band(a, "side_effect") for a in side_w.arousal]})

    effects = []
    for name, g in side_m.groupby("aspect"):
        bands = _bands(g.arousal)
        effects.append({"name": name, "share": g.review_id.nunique() / n, "bands": bands,
                        "group": max(bands, key=bands.get),          # the most common intensity
                        "severity": typical_severity(g.label)})
    order = {"Mild": 0, "Moderate": 1, "Distressing": 2}
    effects.sort(key=lambda e: (order[e["group"]], -e["share"]))   # mild first, then by how common

    ratings = sub.drop_duplicates("review_id").set_index("review_id").rating
    distressing = set(side_w[[intensity_band(a, "side_effect") == "Distressing" for a in side_w.arousal]].review_id)
    if not len(whole):        # older files: fall back to keyword-found severe side effects
        distressing = set(side_m[side_m.label == "Severe"].review_id)
    mismatch = sorted(rid for rid in distressing if ratings[rid] >= 9)

    quotes, used = [], set()
    order = {"Severe": 0, "Moderate": 1, "Mild": 2}
    for _, row in side_m.sort_values("label", key=lambda s: s.map(order)).iterrows():
        if row.aspect not in used:
            quotes.append(row)
            used.add(row.aspect)
        if len(quotes) == 3:
            break
    out = {"n": n, "tiles": tiles, "intensity": intensity, "dots": dots, "effects": effects,
           "mismatch": mismatch, "quotes": quotes, "avg_stars": float(ratings.mean())}
    if len(whole):
        out.update(_drilldowns(sub, whole, ment, ratings))
    return out


def _effect_group(score):
    return "Effective" if score >= 3.5 else "Moderate" if score >= 2.5 else "Not effective"


def _side_group(score):
    return "Mild or none" if score < 2.5 else "Moderate" if score < 3.5 else "Severe"


def _share_satisfied(table, column, groups):
    """[(group, share of its reviews that are satisfied, number of reviews)] for each group."""
    rows = []
    for name in groups:
        g = table[table[column] == name]
        rows.append((name, float((g.satisfaction >= 6.5).mean()) if len(g) else 0.0, len(g)))
    return rows


def _drilldowns(sub, whole, ment, ratings):
    """Extra data for the effectiveness and satisfaction detail views."""
    table = whole.pivot_table(index="review_id", columns="kind", values="score")
    table["stars"] = ratings.reindex(table.index)
    texts = sub.drop_duplicates("review_id").set_index("review_id").text
    table["text"] = texts.reindex(table.index)

    eff = whole[whole.kind == "effectiveness"].set_index("review_id")
    eff_spans = ment[ment.kind == "effectiveness"].drop_duplicates("review_id").set_index("review_id").span
    eff_dots = pd.DataFrame({"v": eff.valence, "a": eff.arousal, "group": [_effect_group(x) for x in eff.score]})
    eff_q = eff.assign(span=eff_spans.reindex(eff.index), text=texts.reindex(eff.index),
                       stars=ratings.reindex(eff.index)).reset_index().sort_values("score")
    sat = whole[whole.kind == "satisfaction"].set_index("review_id")
    sat_q = sat.assign(text=texts.reindex(sat.index), stars=ratings.reindex(sat.index)).reset_index()

    table["side_group"] = [_side_group(x) for x in table.side_effect]
    table["effect_group"] = [_effect_group(x) for x in table.effectiveness]
    gap = (table.satisfaction - table.stars).abs()
    return {
        "eff_intensity": float(eff.arousal.mean()),
        "eff_dots": eff_dots,
        "eff_best": eff_q.tail(2).iloc[::-1], "eff_worst": eff_q.head(2),
        "sat_intensity": float(sat.arousal.mean()),
        "sat_points": table[["stars", "satisfaction"]].dropna().reset_index(),
        "sat_agree": float((gap <= 2).mean()),
        "sat_by_side": _share_satisfied(table, "side_group", ["Mild or none", "Moderate", "Severe"]),
        "sat_by_effect": _share_satisfied(table, "effect_group", ["Effective", "Moderate", "Not effective"]),
        "sat_best": sat_q.sort_values("score").tail(2).iloc[::-1], "sat_worst": sat_q.sort_values("score").head(2),
    }


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
