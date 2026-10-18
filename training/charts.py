"""Charts for the notebook: training curves, results against Gräßer et al. (2018), the
SemEval-step ablation, and confusion matrices.

Runs are found from file names the notebook writes:
    results/<model>_seed<N>.csv            trained with the SemEval (DimABSA) step
    results/<model>_nostage1_seed<N>.csv   Druglib only, no SemEval step
    results/preds/<same name>.csv          per-review predictions
    ckpts/<model>[_nostage1]/seed<N>/stage<1|2>/training_log.json
"""
import glob
import json
import math
import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from core.registry import MODELS
from core.va_anchors import ASPECT_EFFECT, ASPECT_SAT, ASPECT_SIDE
from training.evaluate import three_class

# Gräßer et al. (2018), 3-class results (the same classes training/evaluate.py uses).
GRASSER = pd.DataFrame([
    ("Druglib test", ASPECT_EFFECT, 0.441, 0.777),
    ("Druglib test", ASPECT_SIDE, 0.601, 0.769),
    ("Druglib test", ASPECT_SAT, 0.285, 0.699),
    ("Drugs.com", ASPECT_SAT, 0.268, 0.701),
], columns=["dataset", "aspect", "kappa_3class", "acc_3class"])

# The four aspect/dataset pairs on the x axis, in order
GROUPS = [("Druglib test", ASPECT_EFFECT, "Effectiveness"),
          ("Druglib test", ASPECT_SIDE, "Side effects"),
          ("Druglib test", ASPECT_SAT, "Satisfaction"),
          ("Drugs.com", ASPECT_SAT, "Satisfaction\n→ Drugs.com")]

GRASSER_COLOR = "#b4b2a9"
COLORS = {("RoBERTa", True): "#2a78d6", ("RoBERTa", False): "#9ec5f0",
          ("BioBERT", True): "#1d9e75", ("BioBERT", False): "#97d8bd"}
METRIC_NAMES = {"kappa_3class": "Cohen's kappa × 100", "acc_3class": "Accuracy (%)"}
METRIC_SHORT = {"kappa_3class": "Cohen's kappa", "acc_3class": "accuracy"}
PLANNED = ["RoBERTa", "BioBERT"]   # the comparison's two models: general and biomedical


def slug(name):
    return name.lower().replace("-", "").replace("_", "")


_BY_SLUG = {slug(n): n for n in MODELS}


def parse_run(stem):
    """'roberta_nostage1_seed42' -> ('RoBERTa', False, 42)."""
    head, _, seed = stem.rpartition("_seed")
    semeval = not head.endswith("_nostage1")
    head = head.removesuffix("_nostage1")
    return _BY_SLUG.get(head, head), semeval, int(seed) if seed.isdigit() else None


def run_label(model, semeval):
    return f"{model} + SemEval" if semeval else f"{model}, no SemEval"


def _color(model, semeval, i):
    return COLORS.get((model, semeval), plt.get_cmap("tab10")(i % 10))


def _order(model, semeval):
    names = list(MODELS)
    return (names.index(model) if model in names else 99, not semeval)


# ------------------------------------------------------------------ loading

def load_results(work):
    """Every results CSV, one row per run x dataset x aspect, averaged over seeds."""
    files = sorted(glob.glob(f"{work}/results/*_seed*.csv"))
    if not files:
        raise FileNotFoundError(f"No results in {work}/results yet. Run the evaluate step first.")
    rows = []
    for f in files:
        model, semeval, seed = parse_run(os.path.basename(f)[:-4])
        rows.append(pd.read_csv(f).assign(model=model, semeval=semeval, seed=seed))
    res = pd.concat(rows, ignore_index=True)
    metrics = ["MAE", "RMSE", "acc_3class", "kappa_3class"]
    out = (res.groupby(["model", "semeval", "dataset", "aspect"], as_index=False)
              .agg(**{m: (m, "mean") for m in metrics}, n=("n", "first"), seeds=("seed", "nunique")))
    out["run"] = [run_label(m, s) for m, s in zip(out.model, out.semeval)]
    return out


def runs_in(res):
    pairs = res[["model", "semeval"]].drop_duplicates().itertuples(index=False)
    return sorted(((m, s) for m, s in pairs), key=lambda p: _order(*p))


def results_table(res):
    """Readable table: one row per run, one column per aspect and dataset."""
    t = res.pivot_table(index="run", columns=["dataset", "aspect"],
                        values=["MAE", "kappa_3class"]).round(3)
    order = [run_label(m, s) for m, s in runs_in(res)]
    return t.reindex(order)


# ------------------------------------------------------------------ charts

def plot_training_curves(work):
    """One row per run; stage 1 (SemEval) and stage 2 (Druglib) side by side."""
    logs = sorted(glob.glob(f"{work}/ckpts/*/seed*/stage*/training_log.json"))
    if not logs:
        print("No training logs found."); return
    runs = {}
    for p in logs:
        stage_dir = os.path.dirname(p)
        seed_dir = os.path.dirname(stage_dir)
        run_dir = os.path.basename(os.path.dirname(seed_dir))
        key = (run_dir, os.path.basename(seed_dir))
        runs.setdefault(key, {})[os.path.basename(stage_dir)] = json.load(open(p))["history"]
    keys = sorted(runs, key=lambda k: (_order(*parse_run(f"{k[0]}_{k[1]}")[:2]), k[1]))

    fig, axes = plt.subplots(len(keys), 2, figsize=(11, 3.1 * len(keys)), squeeze=False)
    for row, key in zip(axes, keys):
        model, semeval, seed = parse_run(f"{key[0]}_{key[1]}")
        for ax, stage, title in [(row[0], "stage1", "Stage 1: SemEval (DimABSA)"),
                                 (row[1], "stage2", "Stage 2: Druglib")]:
            hist = runs[key].get(stage)
            if not hist:
                ax.axis("off")
                ax.text(0.5, 0.5, "No SemEval step in this run" if stage == "stage1" else "Not run yet",
                        ha="center", va="center", color="#898781", transform=ax.transAxes)
                continue
            ep = [h["epoch"] for h in hist]
            ax.plot(ep, [math.sqrt(h["train_loss"]) for h in hist], "-o", ms=3, color="#2a78d6",
                    label="Training error (√loss)")
            ax.plot(ep, [h["rmse_v"] for h in hist], "--o", ms=3, color="#eb6834",
                    label="Validation error, valence")
            arousal = [h["rmse_a"] for h in hist]
            if not all(np.isnan(a) for a in arousal):
                ax.plot(ep, arousal, ":o", ms=3, color="#7f77dd", label="Validation error, arousal")
            best = min(range(len(hist)), key=lambda i: hist[i]["score"])
            ax.plot(ep[best], hist[best]["rmse_v"], "o", ms=10, mfc="none", mec="#eb6834", mew=2,
                    label="Best epoch (saved)")
            ax.set_title(f"{run_label(model, semeval)}, seed {seed}  ·  {title}", fontsize=10)
            ax.set_xlabel("Epoch"); ax.set_ylabel("RMSE (1–9 scale)")
            ax.set_xticks(ep); ax.grid(alpha=0.3); ax.spines[["top", "right"]].set_visible(False)
    handles, labels = {}, {}
    for ax in axes.flat:
        for h, l in zip(*ax.get_legend_handles_labels()):
            handles.setdefault(l, h)
    fig.legend(handles.values(), handles.keys(), loc="upper center", ncol=4, frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    plt.show()


def show_transfer_grid(res, metric="kappa_3class"):
    """The headline: Druglib -> Drugs.com satisfaction, model x SemEval step."""
    dc = res[(res.dataset == "Drugs.com") & (res.aspect == ASPECT_SAT)]
    models = [m for m in MODELS if m in set(res.model) | set(PLANNED)]
    grid = pd.DataFrame(index=models, columns=["With SemEval step", "Without"], dtype=float)
    for r in dc.itertuples():
        grid.loc[r.model, "With SemEval step" if r.semeval else "Without"] = getattr(r, metric) * 100
    g = GRASSER[(GRASSER.dataset == "Drugs.com")][metric].iloc[0] * 100
    print(f"Druglib → Drugs.com satisfaction, {METRIC_NAMES[metric]}  (Gräßer et al.: {g:.1f};"
          " blank = not run yet)")
    return grid.round(1)


def plot_comparison(res, metric="kappa_3class"):
    """Grouped bars: Gräßer et al. plus every run, for each aspect."""
    runs = runs_in(res)
    series = [("Gräßer et al. (2018)", GRASSER, GRASSER_COLOR)]
    series += [(run_label(m, s), res[(res.model == m) & (res.semeval == s)], _color(m, s, i))
               for i, (m, s) in enumerate(runs)]
    x = np.arange(len(GROUPS)); width = 0.8 / len(series)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    for i, (label, df, color) in enumerate(series):
        vals = []
        for ds, asp, _ in GROUPS:
            hit = df[(df.dataset == ds) & (df.aspect == asp)]
            vals.append(hit[metric].iloc[0] * 100 if len(hit) else np.nan)
        bars = ax.bar(x - 0.4 + width * (i + 0.5), vals, width * 0.92, label=label, color=color)
        ax.bar_label(bars, fmt="%.1f", fontsize=7, padding=2)
    ax.set_xticks(x, [g[2] for g in GROUPS]); ax.set_ylabel(METRIC_NAMES[metric])
    ax.set_ylim(0, 100 if metric == "acc_3class" else 75)
    ax.legend(frameon=False, fontsize=8, ncol=min(len(series), 5), loc="upper center",
              bbox_to_anchor=(0.5, 1.13))
    ax.grid(axis="y", alpha=0.3); ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); plt.show()


def plot_ablation(res, metric="kappa_3class"):
    """What the SemEval step adds: (with) minus (without), per model and aspect.
    Bars above zero mean learning valence-arousal on SemEval first helped."""
    both = [m for m in MODELS if {True, False} <= set(res[res.model == m].semeval)]
    if not both:
        print("Ablation needs a model trained both with and without the SemEval step "
              "(sections 4 and 6)."); return
    x = np.arange(len(GROUPS)); width = 0.8 / len(both)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for i, m in enumerate(both):
        diffs = []
        for ds, asp, _ in GROUPS:
            sel = res[(res.model == m) & (res.dataset == ds) & (res.aspect == asp)]
            w, wo = sel[sel.semeval][metric], sel[~sel.semeval][metric]
            diffs.append((w.iloc[0] - wo.iloc[0]) * 100 if len(w) and len(wo) else np.nan)
        bars = ax.bar(x - 0.4 + width * (i + 0.5), diffs, width * 0.9, label=m,
                      color=_color(m, True, i))
        ax.bar_label(bars, fmt="%+.1f", fontsize=8, padding=2)
    ax.axhline(0, color="#5f5e5a", lw=1)
    ax.set_xticks(x, [g[2] for g in GROUPS])
    ax.set_ylabel(f"Change in {METRIC_SHORT[metric]} (× 100)\nfrom adding the SemEval step")
    ax.legend(frameon=False, fontsize=9)
    ax.grid(axis="y", alpha=0.3); ax.spines[["top", "right"]].set_visible(False)
    lo, hi = ax.get_ylim(); pad = max(abs(lo), abs(hi)) * 0.2 + 1
    ax.set_ylim(min(lo, 0) - pad, max(hi, 0) + pad)
    fig.tight_layout(); plt.show()


def _confusion(gold, pred, n):
    m = np.zeros((n, n), int)
    for g, p in zip(gold, pred):
        m[g, p] += 1
    return m


def plot_confusion(preds_csv, title=None):
    """Actual vs predicted, per aspect. Effectiveness and side effects on Druglib's five levels;
    satisfaction (1-10) in Gräßer et al.'s three classes. Shading is the share of each actual row."""
    df = pd.read_csv(preds_csv)
    panels = []
    for ds, asp, short in [("Druglib test", ASPECT_EFFECT, "Effectiveness"),
                           ("Druglib test", ASPECT_SIDE, "Side effects"),
                           ("Druglib test", ASPECT_SAT, "Satisfaction"),
                           ("Drugs.com", ASPECT_SAT, "Satisfaction → Drugs.com")]:
        d = df[(df.dataset == ds) & (df.aspect == asp)]
        if not len(d):
            continue
        if asp == ASPECT_SAT:
            g, p = three_class(asp, d.gold), three_class(asp, d.pred)
            ticks = ["1–4", "5–6", "7–10"]
        else:
            g = d.gold.round().clip(1, 5).astype(int).to_numpy() - 1
            p = d.pred.round().clip(1, 5).astype(int).to_numpy() - 1
            ticks = ["1", "2", "3", "4", "5"]
        panels.append((f"{short}\n({ds}, n={len(d):,})", _confusion(g, p, len(ticks)), ticks))
    fig, axes = plt.subplots(1, len(panels), figsize=(4 * len(panels), 4.1), squeeze=False)
    for ax, (name, m, ticks) in zip(axes[0], panels):
        share = m / m.sum(1, keepdims=True).clip(min=1)
        ax.imshow(share, cmap="Blues", vmin=0, vmax=1)
        for i in range(len(ticks)):
            for j in range(len(ticks)):
                ax.text(j, i, m[i, j], ha="center", va="center", fontsize=8,
                        color="white" if share[i, j] > 0.55 else "#2c2c2a")
        ax.set_xticks(range(len(ticks)), ticks); ax.set_yticks(range(len(ticks)), ticks)
        ax.set_xlabel("Predicted"); ax.set_ylabel("Actual"); ax.set_title(name, fontsize=10)
    if title:
        fig.suptitle(title, fontsize=11)
    fig.tight_layout(); plt.show()
