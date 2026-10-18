"""Evaluation on the rating scales people actually understand.

Druglib test split: every review has patient ratings for all three aspects.
Drugs.com: the star rating checks Satisfaction for every review; Effectiveness and
Side-effect severity need a small hand-labeled CSV (Drugs.com has no aspect labels).

Reported per aspect: MAE and RMSE on the rating scale, plus 3-class accuracy and
Cohen's kappa using Gräßer et al. (2018)'s classes, so results compare to their baseline.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score

from core.va_anchors import (ASPECT_EFFECT, ASPECT_SAT, ASPECT_SIDE, valence_to_effectiveness,
                             valence_to_satisfaction, valence_to_side_effects)
from training.model import predict_va

TO_SCALE = {ASPECT_EFFECT: valence_to_effectiveness, ASPECT_SIDE: valence_to_side_effects,
            ASPECT_SAT: valence_to_satisfaction}


def three_class(aspect, rating):
    """Gräßer et al.'s classes. Effectiveness/side effects: 1 | 2-3 | 4-5. Satisfaction: <=4 | 5-6 | >=7."""
    r = np.asarray(rating, dtype=float)
    if aspect == ASPECT_SAT:
        return np.digitize(r, [4.5, 6.5])
    return np.digitize(np.round(r), [1.5, 3.5])


def score_block(aspect, pred, gold):
    pred, gold = np.asarray(pred, float), np.asarray(gold, float)
    err = pred - gold
    pc, gc = three_class(aspect, pred), three_class(aspect, gold)
    return {"aspect": aspect, "n": len(gold),
            "MAE": round(float(np.abs(err).mean()), 3),
            "RMSE": round(float(np.sqrt((err ** 2).mean())), 3),
            "acc_3class": round(float(accuracy_score(gc, pc)), 3),
            "kappa_3class": round(float(cohen_kappa_score(gc, pc)), 3)}


def _predict_scale(model, tok, texts, aspect, max_length):
    va = predict_va(model, tok, list(texts), [aspect] * len(texts), max_length=max_length)
    return [TO_SCALE[aspect](v) for v, _ in va]


def _preds(dataset, aspect, pred, gold):
    """Per-review predictions on the rating scale, for confusion matrices."""
    return pd.DataFrame({"dataset": dataset, "aspect": aspect,
                         "gold": np.asarray(gold, float), "pred": np.asarray(pred, float)})


def evaluate_druglib(model, tok, test_df, max_length=256):
    """Score each text field with its aspect, as in the original viewer design.
    Returns (metrics table, per-review predictions)."""
    blocks, preds = [], []
    for field, aspect, gold_col in [("benefitsReview", ASPECT_EFFECT, "eff_level"),
                                    ("sideEffectsReview", ASPECT_SIDE, "side_level"),
                                    ("commentsReview", ASPECT_SAT, "rating")]:
        df = test_df[(test_df[field] != "") & test_df[gold_col].notna()]
        pred = _predict_scale(model, tok, df[field], aspect, max_length)
        blocks.append(score_block(aspect, pred, df[gold_col]))
        preds.append(_preds("Druglib test", aspect, pred, df[gold_col]))
    return pd.DataFrame(blocks).assign(dataset="Druglib test"), pd.concat(preds, ignore_index=True)


def evaluate_drugscom(model, tok, drugscom_df=None, handlabels_df=None, max_length=256):
    """drugscom_df: columns text, rating (1-10). handlabels_df: columns text, effectiveness (1-5),
    side_effects (1-5); either may be None. Whole review text is scored for every aspect.
    Returns (metrics table, per-review predictions)."""
    blocks, preds = [], []
    if drugscom_df is not None and len(drugscom_df):
        pred = _predict_scale(model, tok, drugscom_df["text"], ASPECT_SAT, max_length)
        blocks.append(score_block(ASPECT_SAT, pred, drugscom_df["rating"]))
        preds.append(_preds("Drugs.com", ASPECT_SAT, pred, drugscom_df["rating"]))
    if handlabels_df is not None and len(handlabels_df):
        for aspect, col in [(ASPECT_EFFECT, "effectiveness"), (ASPECT_SIDE, "side_effects")]:
            df = handlabels_df[handlabels_df[col].notna()]
            pred = _predict_scale(model, tok, df["text"], aspect, max_length)
            blocks.append(score_block(aspect, pred, df[col]))
            preds.append(_preds("Drugs.com", aspect, pred, df[col]))
    return (pd.DataFrame(blocks).assign(dataset="Drugs.com"),
            pd.concat(preds, ignore_index=True) if preds else pd.DataFrame())
