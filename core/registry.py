"""Model registry. Swapping or adding a model means editing MODELS only.

Set "ckpt" to your fine-tuned checkpoint (a Hugging Face Hub repo such as
"your-team/drugreview-deberta", or a local folder). While every ckpt is
None, the app runs on a keyword-based fake scorer so the UI works end to end.
"""
import zlib

from core.aspects import extract
from core.labels import to_label

MODELS = {
    "DeBERTa-v3":   {"hf_id": "microsoft/deberta-v3-base", "ckpt": None,
                     "domain": "General web text"},
    "ModernBERT":   {"hf_id": "answerdotai/ModernBERT-base", "ckpt": None,
                     "domain": "General web text and code"},
    "RoBERTa":      {"hf_id": "roberta-base", "ckpt": None,
                     "domain": "General web text"},
    "PubMedBERT":   {"hf_id": "microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract", "ckpt": None,
                     "domain": "PubMed abstracts"},
    "BioBERT":      {"hf_id": "dmis-lab/biobert-base-cased-v1.2", "ckpt": None,
                     "domain": "PubMed and PMC articles"},
    "ClinicalBERT": {"hf_id": "emilyalsentzer/Bio_ClinicalBERT", "ckpt": None,
                     "domain": "Clinical notes (MIMIC-III)"},
}
MODEL_NAMES = list(MODELS)
USE_FAKE = all(cfg["ckpt"] is None for cfg in MODELS.values())


class AspectScorer:
    """A fine-tuned encoder with a 2-output regression head: (valence, arousal).

    Input is a sentence pair (review text, aspect name), the DimABSA
    subtask 1 format. Train it with num_labels=2 and an MSE loss.
    """

    def __init__(self, ckpt):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tok = AutoTokenizer.from_pretrained(ckpt)
        self.model = AutoModelForSequenceClassification.from_pretrained(ckpt).to(self.device).eval()

    def score(self, text, aspects):
        enc = self.tok([text] * len(aspects), aspects, truncation=True, max_length=512,
                       padding=True, return_tensors="pt").to(self.device)
        with self.torch.no_grad():
            out = self.model(**enc).logits.clamp(1, 9).cpu().tolist()
        return [(round(v, 1), round(a, 1)) for v, a in out]


# ---- fake scorer: keyword rules, used until real checkpoints exist ----
_STRONG = ["severe", "terrible", "unbearable", "awful", "horrible", "worst", "couldn't",
           "nothing at all", "not worth", "exhausted", "barely"]
_MILD = ["mild", "slight", "a little", "faded", "went away", "first week", "first two weeks"]
_GOOD = ["stopped my", "lifted", "better", "helped", "works", "worked", "finally"]
_NONE = ["no change", "didn't help", "did not help", "no difference", "didn't work", "no effect"]


def _clamp(x):
    return max(1.0, min(9.0, x))


def fake_va(span, kind, model_name):
    low = span.lower()
    if kind == "effectiveness":
        if any(c in low for c in _NONE):
            v, a = 2.5, 4.5
        elif any(c in low for c in _GOOD):
            v, a = 7.4, 6.0
        else:
            v, a = 5.2, 4.5
    else:
        if any(c in low for c in _STRONG):
            v, a = 2.2, 6.8
        elif any(c in low for c in _MILD):
            v, a = 4.3, 3.2
        else:
            v, a = 3.6, 5.0
    jitter = (zlib.crc32((model_name + span).encode()) % 9 - 4) / 10  # stable per model
    return round(_clamp(v + jitter), 1), round(_clamp(a + jitter / 2), 1)


class Predictor:
    """What the app calls. Same interface whether the backend is real or fake."""

    def __init__(self, name):
        self.name = name
        ckpt = MODELS[name]["ckpt"]
        self.backend = AspectScorer(ckpt) if ckpt else None

    def _va(self, text, items):
        if self.backend:
            return self.backend.score(text, [i["aspect"] for i in items])
        return [fake_va(i["span"], i["kind"], self.name) for i in items]

    def predict(self, text):
        """Find aspects in a review and score each: [{aspect, kind, span, valence, arousal, label}]."""
        items = extract(text)
        for item, (v, a) in zip(items, self._va(text, items)):
            item.update(valence=v, arousal=a)
            item["label"] = to_label(item)
        return items

    def score_field(self, text, aspect, kind):
        """Score one Druglib text field for one aspect. Returns (valence, arousal)."""
        item = {"aspect": aspect, "kind": kind, "span": text}
        return self._va(text, [item])[0]
