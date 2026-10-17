"""Load DimABSA and Druglib into one format: (text, aspect) pairs with VA targets.

Every example is a dict:
    {"text": str, "aspect": str, "v": float|None, "a": float|None, "group": str}
v/a of None means "no label" and is masked out of the loss. "group" keeps rows
from the same review together when splitting train/validation.
"""
import glob
import json
import os
import random

import pandas as pd
import torch
from torch.utils.data import Dataset

from core.va_anchors import (ASPECT_EFFECT, ASPECT_SAT, ASPECT_SIDE, EFFECT_LEVELS, EFFECT_VA,
                             SIDE_LEVELS, SIDE_VA, satisfaction_va)


# ----------------------------------------------------------------- DimABSA (stage 1)

def _parse_va(va):
    v, a = va.split("#")
    return float(v), float(a)


def _aspect_text(item):
    """The aspect term, or for implicit aspects (Aspect "NULL") the category in words:
    "RESTAURANT#GENERAL" -> "restaurant general". Those sentence-level judgments resemble
    our drug aspects ("Effectiveness", "Satisfaction"), so they are kept, not dropped."""
    aspect = item.get("Aspect")
    if aspect and aspect != "NULL":
        return aspect
    category = item.get("Category")
    if category and category != "NULL":
        return category.replace("#", " ").replace("_", " ").lower()
    return None


def _dimabsa_rows(record):
    """One JSONL record -> pair examples. Handles subtask 1 (Aspect_VA) and the
    triplet/quadruplet ("alltasks") files, which carry VA per aspect."""
    text, rid = record["Text"], str(record.get("ID", ""))
    items = (record.get("Aspect_VA") or record.get("Quadruplet") or record.get("Triplet") or [])
    rows = []
    for it in items:
        aspect = _aspect_text(it)
        if "VA" not in it or not aspect:          # e.g. categorical files have Polarity, not VA
            continue
        v, a = _parse_va(it["VA"])
        rows.append({"text": text, "aspect": aspect, "v": v, "a": a, "group": rid})
    return rows


def load_dimabsa(paths):
    """paths: list of JSONL files (or one folder; every *.jsonl with VA labels in it is used).
    Exact duplicates (same sentence, aspect and scores) are removed, so passing the same file
    twice, as the task repo's identical subtask folders invite, doesn't double-count data."""
    if isinstance(paths, str) and os.path.isdir(paths):
        paths = sorted(glob.glob(os.path.join(paths, "**", "*.jsonl"), recursive=True))
    rows, seen = [], set()
    for p in paths:
        with open(p, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                for r in _dimabsa_rows(json.loads(line)):
                    key = (r["group"], r["text"], r["aspect"], r["v"], r["a"])
                    if key not in seen:
                        seen.add(key)
                        rows.append(r)
    print(f"DimABSA: {len(rows):,} aspect examples from {len(paths)} file(s)")
    return rows


# ----------------------------------------------------------------- Druglib (stage 2)

def load_druglib_split(path):
    """One raw Druglib TSV (drugLibTrain_raw.tsv or drugLibTest_raw.tsv) as a DataFrame."""
    df = pd.read_csv(path, sep="\t")
    df = df.rename(columns={df.columns[0]: "review_id"})
    for col in ["benefitsReview", "sideEffectsReview", "commentsReview"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["eff_level"] = df["effectiveness"].map(EFFECT_LEVELS)
    df["side_level"] = df["sideEffects"].map(SIDE_LEVELS)
    return df


def druglib_pairs(df):
    """Each review -> up to three pairs, one per text field, as in the original viewer design:
    benefits -> Effectiveness, side effects -> Side-effect severity, comments -> Satisfaction."""
    rows = []
    for r in df.itertuples():
        gid = f"druglib-{r.review_id}"
        if r.benefitsReview and pd.notna(r.eff_level):
            v, a = EFFECT_VA[int(r.eff_level)]
            rows.append({"text": r.benefitsReview, "aspect": ASPECT_EFFECT, "v": v, "a": a, "group": gid})
        if r.sideEffectsReview and pd.notna(r.side_level):
            v, a = SIDE_VA[int(r.side_level)]
            rows.append({"text": r.sideEffectsReview, "aspect": ASPECT_SIDE, "v": v, "a": a, "group": gid})
        if r.commentsReview and pd.notna(r.rating):
            v, a = satisfaction_va(float(r.rating))
            rows.append({"text": r.commentsReview, "aspect": ASPECT_SAT, "v": v, "a": a, "group": gid})
    return rows


# ----------------------------------------------------------------- shared

def split_by_group(rows, val_fraction=0.1, seed=42):
    """Validation slice cut from the training data only, keeping each review's rows together."""
    groups = sorted({r["group"] for r in rows})
    random.Random(seed).shuffle(groups)
    val_groups = set(groups[: max(1, int(len(groups) * val_fraction))])
    train = [r for r in rows if r["group"] not in val_groups]
    val = [r for r in rows if r["group"] in val_groups]
    return train, val


class PairDataset(Dataset):
    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        return self.rows[i]


def make_collate(tokenizer, max_length=256):
    """Tokenize (text, aspect) as a sentence pair; build targets plus a mask for missing labels."""
    def collate(batch):
        enc = tokenizer([b["text"] for b in batch], [b["aspect"] for b in batch],
                        truncation="only_first", max_length=max_length, padding=True,
                        return_tensors="pt")
        targets = torch.tensor([[b["v"] or 0.0, b["a"] or 0.0] for b in batch], dtype=torch.float)
        mask = torch.tensor([[b["v"] is not None, b["a"] is not None] for b in batch], dtype=torch.float)
        enc["targets"], enc["mask"] = targets, mask
        return enc
    return collate
