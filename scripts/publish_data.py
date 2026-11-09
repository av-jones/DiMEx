"""Upload the app's data files to a PRIVATE Hugging Face dataset repo (created if needed).

    python scripts/publish_data.py your-hf-username/dimex-data

Uploads whichever of these exist in data/: predictions.parquet (Drugs.com, from batch_score.py) and
druglib_predictions.parquet (from score_druglib.py). Then, in Streamlit Cloud's secrets, set
DIMEX_DATA_REPO to the same repo name and HF_TOKEN to a read token.
"""
import sys
from pathlib import Path

from huggingface_hub import HfApi

DATA = Path(__file__).resolve().parent.parent / "data"
repo = sys.argv[1]
api = HfApi()
api.create_repo(repo, repo_type="dataset", private=True, exist_ok=True)
for name in ["predictions.parquet", "druglib_predictions.parquet"]:
    if (DATA / name).exists():
        api.upload_file(path_or_fileobj=str(DATA / name), path_in_repo=name, repo_id=repo, repo_type="dataset")
        print(f"Uploaded {name} to {repo} (private)")
    else:
        print(f"Skipped {name}: not in data/")
