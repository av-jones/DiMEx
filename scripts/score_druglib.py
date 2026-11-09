"""Score the Druglib test split with the trained model and save data/druglib_predictions.parquet.

Run in Colab (GPU) after training, with the checkpoint set:
    DIMEX_CHECKPOINT=ckpts/roberta/stage2 python scripts/score_druglib.py path/to/drugLibTest_raw.tsv
Then upload it with scripts/publish_data.py. The app's Druglib page and model card read it.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import druglib  # noqa: E402
from core.registry import APP_MODEL, Predictor, is_real  # noqa: E402

if __name__ == "__main__":
    if not is_real(APP_MODEL):
        sys.exit("No checkpoint set. Set DIMEX_CHECKPOINT to the trained model folder or Hub repo.")
    df = druglib.score(druglib._tidy(pd.read_csv(sys.argv[1], sep="\t")), Predictor(APP_MODEL))
    out = Path(__file__).resolve().parent.parent / "data" / druglib.PRED_FILE
    out.parent.mkdir(exist_ok=True)
    df.to_parquet(out, index=False)
    print(f"Saved {len(df):,} reviews to {out}")
    print(druglib.metrics(df).round(3).to_string(index=False))
