"""Command line for the whole model pipeline. Run from the repo root.

  Stage 1: learn the valence-arousal scale on DimABSA (English restaurant + laptop)
    python -m training.run stage1 --model DeBERTa-v3 --dimabsa data/dimabsa --out ckpts/deberta/stage1

  Stage 2: adapt to drug reviews on Druglib (validation slice cut from the train file only)
    python -m training.run stage2 --init ckpts/deberta/stage1 --druglib data/druglib --out ckpts/deberta/stage2

  Evaluate: Druglib test split, plus Drugs.com if given
    python -m training.run evaluate --ckpt ckpts/deberta/stage2 --druglib data/druglib \
        --drugscom data/drugscom/drugsComTest_raw.tsv --handlabels data/drugscom_handlabels.csv \
        --out results/deberta.csv

  Push a checkpoint to the Hugging Face Hub (then set it as "ckpt" in core/registry.py)
    python -m training.run push --ckpt ckpts/deberta/stage2 --repo your-team/dimex-deberta

--model accepts a name from core/registry.py (e.g. "PubMedBERT") or any Hugging Face model id.
--limit N uses only N training examples: a quick smoke test before a full run.
"""
import argparse
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.registry import MODELS  # noqa: E402
from training.data import (druglib_pairs, load_dimabsa, load_druglib_split,  # noqa: E402
                           split_by_group)
from training.train import TrainConfig, train  # noqa: E402


def resolve(name):
    return MODELS[name]["hf_id"] if name in MODELS else name


def find(folder, pattern):
    hits = [f for f in os.listdir(folder) if pattern.lower() in f.lower()]
    if not hits:
        sys.exit(f"No file matching '{pattern}' in {folder}")
    return os.path.join(folder, sorted(hits)[0])


def limit(rows, n):
    return rows[:n] if n else rows


def common_args(p):
    p.add_argument("--out", required=True)
    p.add_argument("--epochs", type=int, default=4)
    p.add_argument("--batch_size", type=int, default=16)
    p.add_argument("--lr", type=float, default=2e-5)
    p.add_argument("--max_length", type=int, default=256)
    p.add_argument("--grad_accum", type=int, default=1)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--precision", choices=["fp32", "bf16"], default="fp32",
                   help="bf16 is faster on A100/L4 but was unstable with DeBERTa-v3")


def main():
    ap = argparse.ArgumentParser(description="DiMEx model pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s1 = sub.add_parser("stage1", help="train on DimABSA")
    s1.add_argument("--model", required=True)
    s1.add_argument("--dimabsa", required=True, nargs="+", help="folder, or JSONL files with VA labels")
    s1.add_argument("--dimabsa_dev", nargs="+", help="labeled dev JSONL; default: 10%% of train")
    common_args(s1)

    s2 = sub.add_parser("stage2", help="train on Druglib")
    s2.add_argument("--init", required=True, help="stage-1 checkpoint folder, or a model name to skip stage 1")
    s2.add_argument("--druglib", required=True, help="folder with drugLibTrain_raw.tsv")
    common_args(s2)

    ev = sub.add_parser("evaluate", help="score a checkpoint")
    ev.add_argument("--ckpt", required=True)
    ev.add_argument("--druglib", help="folder with drugLibTest_raw.tsv")
    ev.add_argument("--drugscom", help="Drugs.com TSV (drugsComTest_raw.tsv)")
    ev.add_argument("--drugscom_sample", type=int, default=5000, help="rows of Drugs.com to score")
    ev.add_argument("--handlabels", help="CSV: text, effectiveness (1-5), side_effects (1-5)")
    ev.add_argument("--max_length", type=int, default=256)
    ev.add_argument("--out", required=True, help="results CSV")

    pu = sub.add_parser("push", help="upload a checkpoint to the Hugging Face Hub")
    pu.add_argument("--ckpt", required=True)
    pu.add_argument("--repo", required=True)
    pu.add_argument("--public", action="store_true")

    a = ap.parse_args()

    if a.cmd == "stage1":
        src = a.dimabsa[0] if len(a.dimabsa) == 1 else a.dimabsa
        rows = load_dimabsa(src)
        if a.dimabsa_dev:
            train_rows, val_rows = rows, load_dimabsa(a.dimabsa_dev)
        else:
            train_rows, val_rows = split_by_group(rows, seed=a.seed)
        cfg = TrainConfig(model=resolve(a.model), out_dir=a.out, epochs=a.epochs, batch_size=a.batch_size,
                          lr=a.lr, max_length=a.max_length, grad_accum=a.grad_accum, seed=a.seed,
                          precision=a.precision)
        train(cfg, limit(train_rows, a.limit), limit(val_rows, a.limit and max(a.limit // 5, 8)))

    elif a.cmd == "stage2":
        df = load_druglib_split(find(a.druglib, "train"))
        train_rows, val_rows = split_by_group(druglib_pairs(df), seed=a.seed)
        print(f"Druglib: {len(df):,} reviews -> {len(train_rows):,} train / {len(val_rows):,} validation pairs")
        is_ckpt = os.path.isdir(a.init)
        if is_ckpt and not os.path.exists(os.path.join(a.init, "config.json")):
            sys.exit(f"{a.init} has no saved model. Did stage 1 finish and save a checkpoint?")
        cfg = TrainConfig(model=a.init if is_ckpt else resolve(a.init), out_dir=a.out, epochs=a.epochs,
                          batch_size=a.batch_size, lr=a.lr, max_length=a.max_length,
                          grad_accum=a.grad_accum, seed=a.seed, init_bias=not is_ckpt,
                          precision=a.precision)
        train(cfg, limit(train_rows, a.limit), limit(val_rows, a.limit and max(a.limit // 5, 8)))

    elif a.cmd == "evaluate":
        import torch
        from training.evaluate import evaluate_druglib, evaluate_drugscom
        from training.model import load_model
        model, tok = load_model(a.ckpt)
        model.to("cuda" if torch.cuda.is_available() else "cpu")
        tables = []
        if a.druglib:
            tables.append(evaluate_druglib(model, tok, load_druglib_split(find(a.druglib, "test")), a.max_length))
        dc = hl = None
        if a.drugscom:
            dc = pd.read_csv(a.drugscom, sep="\t").rename(columns={"review": "text"})
            dc["text"] = dc["text"].astype(str).str.strip('"').str.replace("&#039;", "'", regex=False)
            dc = dc.sample(min(a.drugscom_sample, len(dc)), random_state=42)
        if a.handlabels:
            hl = pd.read_csv(a.handlabels)
        if dc is not None or hl is not None:
            tables.append(evaluate_drugscom(model, tok, dc, hl, a.max_length))
        results = pd.concat(tables, ignore_index=True).assign(checkpoint=a.ckpt)
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        results.to_csv(a.out, index=False)
        print(results.to_string(index=False))

    elif a.cmd == "push":
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        AutoModelForSequenceClassification.from_pretrained(a.ckpt).push_to_hub(a.repo, private=not a.public)
        AutoTokenizer.from_pretrained(a.ckpt).push_to_hub(a.repo, private=not a.public)
        print(f"Pushed. In core/registry.py set \"ckpt\": \"{a.repo}\"")


if __name__ == "__main__":
    main()
