"""Plain-language explanations for a scored review.

Intensity bands come from arousal (1-9). The "key sentence" for an aspect is the sentence whose
removal changes that aspect's valence the most (leave-one-sentence-out): a simple, model-agnostic
way to show which part of the review drove a score. It explains the score's sensitivity, not the
model's internal reasoning, and the UI says so.
"""
import re

INTENSITY_CUTS = (4.5, 6.3)     # arousal < 4.5 low | < 6.3 moderate | >= 6.3 high


def intensity_band(arousal, kind="side_effect"):
    """Word for an arousal score. Side effects: Mild / Moderate / Distressing; others: Calm / Moderate / Strong."""
    if arousal is None:
        return "Unknown"
    low, high = ("Mild", "Distressing") if kind == "side_effect" else ("Calm", "Strong")
    if arousal < INTENSITY_CUTS[0]:
        return low
    if arousal < INTENSITY_CUTS[1]:
        return "Moderate"
    return high


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [p.strip() for p in parts if len(p.strip()) > 2]


def key_sentences(predictor, text, max_sentences=10):
    """{aspect: (sentence, change in valence)} for reviews with 2+ sentences, else {}."""
    sents = split_sentences(text)
    if len(sents) < 2 or len(sents) > max_sentences:
        return {}
    full = {r["aspect"]: r["valence"] for r in predictor.score_review(text)}
    best = {}
    for i, s in enumerate(sents):
        rest = " ".join(sents[:i] + sents[i + 1:])
        for r in predictor.score_review(rest):
            delta = abs(full[r["aspect"]] - r["valence"])
            if delta > best.get(r["aspect"], (None, 0.0))[1]:
                best[r["aspect"]] = (s, delta)
    return {a: v for a, v in best.items() if v[1] >= 0.1}


def why(kind, valence, arousal):
    """One short line in words, from valence and arousal."""
    tone = "positive" if valence >= 6 else "negative" if valence <= 4 else "mixed"
    band = intensity_band(arousal, kind).lower()
    if kind == "side_effect":
        if valence >= 5.5:
            return "Few or no side-effect complaints."
        if band == "distressing":
            return "Negative and intense: the side effects sound disruptive, not just uncomfortable."
        return f"Negative but {band}: side effects are noticeable without sounding overwhelming."
    if kind == "effectiveness":
        return {"positive": "Describes a clear benefit.", "mixed": "Describes a partial or uncertain benefit.",
                "negative": "Describes little or no benefit."}[tone] + f" Expressed with {band} intensity."
    return {"positive": "Sounds satisfied overall.", "mixed": "Sounds torn overall.",
            "negative": "Sounds dissatisfied overall."}[tone]


def summary_sentence(results):
    """One sentence from the three aspect results (score_review output)."""
    by = {r["kind"]: r for r in results}
    eff, side, sat = by.get("effectiveness"), by.get("side_effect"), by.get("satisfaction")
    if not (eff and side and sat):
        return ""
    e = eff["rating"]
    eff_txt = "Worked well" if e >= 3.5 else "Helped somewhat" if e >= 2.5 else "Didn't help much"
    s = side["rating"]
    band = intensity_band(side["arousal"], "side_effect")
    if s < 1.6:
        side_txt, bad = "with few side effects", False
    elif band == "Distressing" and s >= 2.5:
        side_txt, bad = "the side effects sound **distressing**", True
    elif s >= 3.5:
        side_txt, bad = "the side effects sound severe", True
    else:
        side_txt, bad = "with some side effects", s >= 2.5
    sat_txt = {"Satisfied": "satisfied", "Mixed": "only moderately satisfied",
               "Dissatisfied": "dissatisfied"}[sat["label"]]
    if side_txt.startswith("with"):
        return f"{eff_txt} {side_txt}; the patient sounds {sat_txt}."
    joiner = "but" if (e >= 2.5 and bad) else "and"
    return f"{eff_txt}, {joiner} {side_txt}, so the patient sounds {sat_txt}."
