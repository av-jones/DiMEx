"""Shared mapping between Druglib's patient ratings and valence-arousal (VA) scores.

Training uses it to turn Druglib labels into VA targets; the app uses it to turn
predicted VA back onto Druglib's rating scales. Keeping one table guarantees the
round trip is consistent.

These anchors are a FIRST DRAFT. Calibrate them (e.g. check that predicted VA on
Druglib validation reviews lands near these anchors per class) and report the
final table in the paper. None means "no target": that dimension is masked out of
the loss, so the model learns arousal only from data that actually labels it.
"""
import numpy as np

# Aspect names used both in training pairs (text, aspect) and at inference time.
ASPECT_EFFECT = "Effectiveness"
ASPECT_SIDE = "Side-effect severity"
ASPECT_SAT = "Satisfaction"

# Druglib label text -> ordinal level
EFFECT_LEVELS = {"Ineffective": 1, "Marginally Effective": 2, "Moderately Effective": 3,
                 "Considerably Effective": 4, "Highly Effective": 5}
SIDE_LEVELS = {"No Side Effects": 1, "Mild Side Effects": 2, "Moderate Side Effects": 3,
               "Severe Side Effects": 4, "Extremely Severe Side Effects": 5}

# Ordinal level -> (valence, arousal); arousal None = unknown, masked in the loss.
EFFECT_VA = {1: (2.5, None), 2: (4.2, None), 3: (5.5, None), 4: (6.8, None), 5: (7.8, None)}
SIDE_VA = {1: (6.0, 3.0), 2: (4.5, 3.5), 3: (3.6, 5.0), 4: (2.6, 6.5), 5: (1.8, 7.5)}


def satisfaction_va(rating):
    """Druglib/Drugs.com 1-10 rating -> (valence, None)."""
    return 1 + 8 * (rating - 1) / 9, None


# ---- inverse: predicted valence -> rating scale (piecewise linear between anchors) ----

def _inverse(table, v):
    levels = sorted(table)
    vs = np.array([table[k][0] for k in levels])
    ks = np.array(levels, dtype=float)
    order = np.argsort(vs)                     # np.interp needs increasing x
    return float(np.interp(v, vs[order], ks[order]))


def valence_to_effectiveness(v):
    return _inverse(EFFECT_VA, v)              # 1-5, higher = more effective


def valence_to_side_effects(v):
    return _inverse(SIDE_VA, v)                # 1-5, higher = more severe


def valence_to_satisfaction(v):
    return float(np.clip(1 + 9 * (v - 1) / 8, 1, 10))
