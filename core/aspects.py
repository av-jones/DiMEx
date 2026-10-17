"""Find which aspects a review talks about, and the sentence (span) for each.

This lexicon extractor is a stand-in. Later it can be replaced by a
DimASTE-style model that extracts (aspect, opinion) spans directly.
"""
import re

SIDE_EFFECTS = {
    "Nausea": ["nausea", "nauseous", "queasy", "sick to my stomach"],
    "Trouble sleeping": ["insomnia", "can't sleep", "cannot sleep", "trouble sleeping",
                         "harder to sleep", "wide awake", "sleep through"],
    "Emotional numbness": ["numb", "emotionally flat", "feel nothing", "emotionless", "blunted"],
    "Fatigue": ["tired", "exhausted", "fatigue", "drowsy"],
    "Headache": ["headache"],
    "Weight gain": ["weight gain", "gained"],
    "Dizziness": ["dizzy", "dizziness", "lightheaded"],
    "Sexual side effects": ["libido", "sex drive", "sexual"],
}

EFFECT_CUES = ["work", "help", "stopped my", "better", "improv", "lifted", "edge off",
               "no change", "no difference", "finally"]


def split_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def extract(text):
    """Return [{aspect, kind, span}], effectiveness first, then side effects."""
    sentences = split_sentences(text)
    effect_span, found, seen = None, [], set()
    for s in sentences:
        low = s.lower()
        hit = False
        for name, cues in SIDE_EFFECTS.items():
            if name not in seen and any(c in low for c in cues):
                found.append({"aspect": name, "kind": "side_effect", "span": s})
                seen.add(name)
                hit = True
        if effect_span is None and not hit and any(c in low for c in EFFECT_CUES):
            effect_span = s
    if effect_span is None and sentences:
        effect_span = sentences[0]
    items = [{"aspect": "Effectiveness", "kind": "effectiveness", "span": effect_span or ""}]
    return items + found
