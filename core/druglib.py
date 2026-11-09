"""Druglib test split: patients' own ratings next to the model's predictions, for the Druglib page and the
model card.

Each Druglib review has three text fields, each rated by the patient:
    benefits      -> effectiveness, 1-5 (5 = highly effective)
    side effects  -> side-effect severity, 1-5 (5 = extremely severe)
    comments      -> overall satisfaction, 1-10

Where the data comes from, in order:
    1. druglib_predictions.parquet in the private data repo, made in Colab with the trained model
       (python scripts/score_druglib.py, see the notebook's last section)
    2. drugLibTest_raw.tsv from DIMEX_DRUGLIB_DIR or downloaded from UCI, scored here with the app's model
       (the placeholder scorer until a checkpoint is connected)
    3. a few built-in example reviews
Review text is never stored in the GitHub repo.
"""
import io
import os
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from core.registry import APP_MODEL, Predictor, is_real
from core.va_anchors import EFFECT_LEVELS, SIDE_LEVELS

UCI_ZIP = "https://archive.ics.uci.edu/static/public/461/drug+review+dataset+druglib+com.zip"
CACHE = Path.home() / ".cache" / "dimex"
PRED_FILE = "druglib_predictions.parquet"

# (key, text column, display name, kind, scale)
ASPECTS = [("eff", "benefits", "Effectiveness", "effectiveness", 5),
           ("side", "side_effects", "Side effects", "side_effect", 5),
           ("sat", "comment", "Satisfaction", "satisfaction", 10)]
LEVEL_NAMES = {"eff": {v: k.replace(" Effective", "").replace("Ineffective", "Not effective")
                       for k, v in EFFECT_LEVELS.items()},
               "side": {v: k.replace(" Side Effects", "").replace("No", "None") for k, v in SIDE_LEVELS.items()}}


def _raw_test():
    """drugLibTest_raw.tsv as a DataFrame, or None if it can't be found or downloaded."""
    from core.settings import setting
    folder = setting("DIMEX_DRUGLIB_DIR")
    if folder and (Path(folder) / "drugLibTest_raw.tsv").exists():
        return pd.read_csv(Path(folder) / "drugLibTest_raw.tsv", sep="\t")
    cached = CACHE / "drugLibTest_raw.tsv"
    if not cached.exists():
        try:
            import urllib.request
            with urllib.request.urlopen(UCI_ZIP, timeout=30) as r:
                z = zipfile.ZipFile(io.BytesIO(r.read()))
            name = next(n for n in z.namelist() if n.endswith("drugLibTest_raw.tsv"))
            CACHE.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(z.read(name))
        except Exception as e:
            print(f"[dimex] couldn't download Druglib from UCI: {type(e).__name__}")
            return None
    return pd.read_csv(cached, sep="\t")


def _tidy(raw):
    """Raw Druglib columns -> review_id, drug, condition, the three texts and the patient's ratings."""
    df = pd.DataFrame({
        "review_id": raw[raw.columns[0]].astype(int),
        "drug": raw["urlDrugName"].astype(str).str.replace("-", " ").str.title(),
        "condition": raw["condition"].fillna("").astype(str).str.strip().str.capitalize(),
        "benefits": raw["benefitsReview"].fillna("").astype(str).str.strip(),
        "side_effects": raw["sideEffectsReview"].fillna("").astype(str).str.strip(),
        "comment": raw["commentsReview"].fillna("").astype(str).str.strip(),
        "gold_eff": raw["effectiveness"].map(EFFECT_LEVELS),
        "gold_side": raw["sideEffects"].map(SIDE_LEVELS),
        "gold_sat": pd.to_numeric(raw["rating"], errors="coerce"),
    })
    return df[df.condition != ""].reset_index(drop=True)


_EXAMPLES = pd.DataFrame([
    {"review_id": 412, "drug": "Zoloft", "condition": "Depression", "gold_eff": 4, "gold_side": 3, "gold_sat": 7,
     "benefits": "My mood lifted after about five weeks. I could focus at work again.",
     "side_effects": "Some nausea and headaches the first two weeks, and it is harder to sleep through the night.",
     "comment": "Took 50mg every morning. Overall it helped a lot, but the sleep issue still bothers me."},
    {"review_id": 877, "drug": "Lexapro", "condition": "Anxiety", "gold_eff": 3, "gold_side": 4, "gold_sat": 3,
     "benefits": "Took the edge off my anxiety but I still had panic attacks at work.",
     "side_effects": "Felt exhausted all day and gained about ten pounds.",
     "comment": "Stopped after four months. Not worth the weight gain for me."},
    {"review_id": 931, "drug": "Lexapro", "condition": "Depression", "gold_eff": 5, "gold_side": 1, "gold_sat": 9,
     "benefits": "Works great, I finally feel like myself again.", "side_effects": "None that I noticed.",
     "comment": "Best medication I have tried. It helped right away."},
    {"review_id": 1002, "drug": "Zoloft", "condition": "Ocd", "gold_eff": 2, "gold_side": 4, "gold_sat": 2,
     "benefits": "No change in my intrusive thoughts after three months.",
     "side_effects": "Severe insomnia and I felt terrible most days.",
     "comment": "Didn't help and the side effects were awful."},
])


def score(df, predictor):
    """Add the model's predictions (pred_*, on the patient's scales) and valence/arousal (v_*, a_*)."""
    from core.labels import va_to_rating
    from core.va_anchors import ASPECT_EFFECT, ASPECT_SAT, ASPECT_SIDE
    names = {"eff": ASPECT_EFFECT, "side": ASPECT_SIDE, "sat": ASPECT_SAT}
    out = df.copy()
    for key, col, _, kind, scale in ASPECTS:
        va_kind = "side_effect" if kind == "side_effect" else "effectiveness"
        vs, as_, preds = [], [], []
        for text in out[col]:
            if not text:
                vs.append(np.nan), as_.append(np.nan), preds.append(np.nan)
                continue
            v, a = predictor.score_field(text, names[key], va_kind)
            vs.append(v), as_.append(a)
            preds.append(round(float(min(scale, max(1, va_to_rating(v, kind)))), 2))
        out[f"v_{key}"], out[f"a_{key}"], out[f"pred_{key}"] = vs, as_, preds
    return out


def load():
    """(reviews with predictions, source) where source is "trained", "placeholder" or "examples"."""
    from core.settings import hf_file
    path = hf_file(PRED_FILE)
    if path:
        return pd.read_parquet(path), "trained"
    raw = _raw_test()
    base = _tidy(raw) if raw is not None else _EXAMPLES
    scored = score(base, Predictor(APP_MODEL))
    if raw is None:
        return scored, "examples"
    return scored, "trained" if is_real(APP_MODEL) else "placeholder"


# ---------------------------------------------------------------- error measures

def three_class(key, r):
    """Gräßer et al.'s classes. Effectiveness/side effects: 1 | 2-3 | 4-5. Satisfaction: <=4 | 5-6 | >=7."""
    r = np.asarray(r, dtype=float)
    return np.digitize(r, [4.5, 6.5]) if key == "sat" else np.digitize(np.round(r), [1.5, 3.5])


def _kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    labels = np.union1d(a, b)
    po = np.mean(a == b)
    pe = sum(np.mean(a == k) * np.mean(b == k) for k in labels)
    return float((po - pe) / (1 - pe)) if pe < 1 else 1.0


def metrics(df):
    """Per aspect: reviews, MAE, RMSE, share within 1 point, 3-class accuracy and Cohen's kappa."""
    rows = []
    for key, _, name, _, scale in ASPECTS:
        d = df[[f"gold_{key}", f"pred_{key}"]].dropna()
        if d.empty:
            continue
        g, p = d[f"gold_{key}"].to_numpy(float), d[f"pred_{key}"].to_numpy(float)
        err = p - g
        gc, pc = three_class(key, g), three_class(key, p)
        rows.append({"Aspect": name, "Scale": f"1–{scale}", "Reviews": len(d),
                     "MAE": float(np.abs(err).mean()), "RMSE": float(np.sqrt((err ** 2).mean())),
                     "Within 1 point": float(np.mean(np.abs(err) <= 1)),
                     "3-class accuracy": float(np.mean(gc == pc)), "Kappa": _kappa(gc, pc)})
    return pd.DataFrame(rows)


def gap(df):
    """Each review's average distance from the patient, as a share of each scale (0 = exact)."""
    parts = [(df[f"pred_{k}"] - df[f"gold_{k}"]).abs() / (s - 1) for k, _, _, _, s in ASPECTS]
    return pd.concat(parts, axis=1).mean(axis=1)
