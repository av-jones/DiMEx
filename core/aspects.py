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


def find_terms(text, effect=True):
    """The words that mark an aspect, for highlighting: [(start, end, aspect, kind)], in text order.
    Side-effect terms always; effectiveness cue words when effect=True. A match runs to the end of its word
    ('help' covers 'helped'), and overlapping matches keep the first."""
    low, hits = text.lower(), []
    groups = [(name, "side_effect", cues) for name, cues in SIDE_EFFECTS.items()]
    if effect:
        groups.append(("Effectiveness", "effectiveness", EFFECT_CUES))
    for name, kind, cues in groups:
        for cue in cues:
            for m in re.finditer(r"\b" + re.escape(cue) + r"\w*", low):
                hits.append((m.start(), m.end(), name, kind))
    hits.sort()
    out, last = [], -1
    for h in hits:
        if h[0] >= last:
            out.append(h)
            last = h[1]
    return out
