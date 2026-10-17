"""The regressor: any Hugging Face encoder with a 2-output head (valence, arousal).

We use AutoModelForSequenceClassification(num_labels=2) instead of a custom
nn.Module so a saved checkpoint loads directly in the app (core/registry.py,
AspectScorer) and pushes to the Hugging Face Hub with no extra code.
"""
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def load_model(name_or_path, num_labels=2):
    tokenizer = AutoTokenizer.from_pretrained(name_or_path)
    model = AutoModelForSequenceClassification.from_pretrained(
        name_or_path, num_labels=num_labels, problem_type="regression",
        ignore_mismatched_sizes=True)          # lets a stage-1 checkpoint or a fresh encoder load
    return model, tokenizer


def init_head_bias(model, value=5.0):
    """Start predictions at the middle of the 1-9 scale instead of 0. Speeds up early training."""
    last = None
    for m in model.modules():
        if isinstance(m, torch.nn.Linear) and m.out_features == 2:
            last = m
    if last is not None and last.bias is not None:
        with torch.no_grad():
            last.bias.fill_(value)


def masked_mse(pred, target, mask):
    """MSE over labeled dimensions only (Druglib often has valence but no arousal)."""
    sq = (pred - target) ** 2 * mask
    return sq.sum() / mask.sum().clamp(min=1.0)


def predict_va(model, tokenizer, texts, aspects, batch_size=32, max_length=256, device=None):
    """Score (text, aspect) pairs. Returns a list of (valence, arousal) clamped to 1-9."""
    device = device or next(model.parameters()).device
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            enc = tokenizer(texts[i:i + batch_size], aspects[i:i + batch_size], truncation="only_first",
                            max_length=max_length, padding=True, return_tensors="pt").to(device)
            out.extend(model(**enc).logits.float().clamp(1, 9).cpu().tolist())
    return [tuple(x) for x in out]
