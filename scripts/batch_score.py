"""Score every Drugs.com review with every model and save data/predictions.parquet.

Run this in Colab (GPU) after training, then upload the parquet file to a
private Hugging Face dataset repo or copy it into data/.

    python scripts/batch_score.py drugsComTrain_raw.tsv drugsComTest_raw.tsv
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.data import PRED_PATH, batch_score  # noqa: E402


def load_drugscom(paths):
    df = pd.concat([pd.read_csv(p, sep="\t") for p in paths], ignore_index=True)
    df = df.rename(columns={"Unnamed: 0": "review_id", "drugName": "drug", "review": "text"})
    df["text"] = df.text.str.strip('"').str.replace("&#039;", "'", regex=False)
    return df.dropna(subset=["condition"])[["review_id", "drug", "condition", "rating", "text"]]


if __name__ == "__main__":
    reviews = load_drugscom(sys.argv[1:])
    preds = batch_score(reviews)
    PRED_PATH.parent.mkdir(exist_ok=True)
    preds.to_parquet(PRED_PATH, index=False)
    print(f"Saved {len(preds):,} rows to {PRED_PATH}")
