"""Save the Drugs.com drug-condition pairs and their review counts to assets/drugscom_pairs.csv.

Only names and counts are saved (no review text), so the file can live in the public repo.
The app uses it to fill the pickers with the real drugs and conditions while scores are placeholders.

    python scripts/export_pairs.py drugsComTrain_raw.tsv drugsComTest_raw.tsv
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.data import PAIRS_PATH, pair_counts  # noqa: E402
from scripts.batch_score import load_drugscom  # noqa: E402

if __name__ == "__main__":
    pairs = pair_counts(load_drugscom(sys.argv[1:]))
    PAIRS_PATH.parent.mkdir(exist_ok=True)
    pairs.to_csv(PAIRS_PATH, index=False)
    print(f"Saved {len(pairs):,} pairs ({pairs.n.sum():,} reviews) to {PAIRS_PATH}")
