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
}


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
