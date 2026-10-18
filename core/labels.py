"""Turn valence-arousal scores (1-9) into the words the UI shows.

The thresholds are a design decision: calibrate them against Druglib's
categorical labels and report the values you choose in the paper.
"""


def effectiveness_label(v):
    if v >= 6.0:
        return "Worked well"
    if v >= 4.5:
        return "Some benefit"
    return "Didn't help"


def severity_label(v, a):
    if v <= 3.0 and a >= 5.5:
        return "Severe"
    if v <= 4.0:
        return "Moderate"
    return "Mild"


def to_label(item):
    if item["kind"] == "effectiveness":
        return effectiveness_label(item["valence"])
    return severity_label(item["valence"], item["arousal"])


def typical_severity(labels):
    """Summarize many per-review severities into one phrase."""
    labels = list(labels)
    if not labels:
        return "Usually mild"
    severe = labels.count("Severe") / len(labels)
    moderate = labels.count("Moderate") / len(labels)
    if severe >= 0.3:
        return "Often severe"
    if severe + moderate >= 0.5:
        return "Moderate"
    return "Usually mild"


_CHIP_COLORS = {
    "Worked well": "green", "Some benefit": "gray", "Didn't help": "red",
    "Severe": "red", "Often severe": "red", "Moderate": "orange",
    "Mild": "gray", "Usually mild": "gray",
    # Druglib's own categories, used for the three trained aspects
    "Highly effective": "green", "Considerably effective": "green", "Moderately effective": "gray",
    "Marginally effective": "orange", "Ineffective": "red",
    "No side effects": "green", "Mild side effects": "gray", "Moderate side effects": "orange",
    "Severe side effects": "red", "Extremely severe side effects": "red",
    "Satisfied": "green", "Mixed": "gray", "Dissatisfied": "red",
}

EFFECT_NAMES = {1: "Ineffective", 2: "Marginally effective", 3: "Moderately effective",
                4: "Considerably effective", 5: "Highly effective"}
SIDE_NAMES = {1: "No side effects", 2: "Mild side effects", 3: "Moderate side effects",
              4: "Severe side effects", 5: "Extremely severe side effects"}


def rating_label(kind, rating):
    """Druglib's category for a predicted rating (effectiveness/side effects 1-5, satisfaction 1-10).
    Satisfaction uses Gräßer et al.'s bands: <=4 | 5-6 | >=7."""
    if kind == "effectiveness":
        return EFFECT_NAMES[int(min(5, max(1, round(rating))))]
    if kind == "side_effect":
        return SIDE_NAMES[int(min(5, max(1, round(rating))))]
    return "Dissatisfied" if rating < 4.5 else "Mixed" if rating < 6.5 else "Satisfied"


def chip(label):
    """Streamlit markdown for a colored label, e.g. :red-background[Severe]."""
    return f":{_CHIP_COLORS.get(label, 'gray')}-background[{label}]"


# Map a valence score back onto Druglib's patient rating scales (model check page).
# Uses the same anchor table as training (core/va_anchors.py), so scores round-trip.
def va_to_rating(v, kind):
    from core.va_anchors import (valence_to_effectiveness, valence_to_satisfaction,
                                 valence_to_side_effects)
    if kind == "effectiveness":          # 1 = ineffective ... 5 = highly effective
        return valence_to_effectiveness(v)
    if kind == "side_effect":            # 1 = none ... 5 = extremely severe
        return valence_to_side_effects(v)
    return valence_to_satisfaction(v)    # satisfaction 1-10
