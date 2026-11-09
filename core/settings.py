"""Deployment settings, read from environment variables or Streamlit secrets (never from the repo).

    HF_TOKEN          Hugging Face read token, for the private model and data repos
    DIMEX_MODEL       which registry entry the app uses (default: RoBERTa)
    DIMEX_CHECKPOINT  private Hugging Face model repo with that model's trained weights,
                      e.g. "av-jones/dimex-roberta"
    DIMEX_DATA_REPO   private Hugging Face dataset repo holding predictions.parquet (Drugs.com) and
                      druglib_predictions.parquet (Druglib test split), e.g. "av-jones/dimex-data"
    DIMEX_DRUGLIB_DIR optional local folder with drugLibTest_raw.tsv (otherwise downloaded from UCI)

On Streamlit Cloud put them in App settings -> Secrets, e.g.  HF_TOKEN = "hf_..."
"""
import os


def setting(key, default=None):
    value = os.environ.get(key)
    if value:
        return value
    try:
        import streamlit as st
        value = st.secrets.get(key)
    except Exception:
        value = None
    return value or default


def hf_file(filename):
    """Download one file from the private data repo (cached by huggingface_hub); None if not set up."""
    repo = setting("DIMEX_DATA_REPO")
    if not repo:
        return None
    try:
        from huggingface_hub import hf_hub_download
        return hf_hub_download(repo, filename, repo_type="dataset", token=setting("HF_TOKEN"))
    except Exception as e:                       # missing file, bad token, offline: fall back quietly
        print(f"[dimex] couldn't fetch {filename} from {repo}: {type(e).__name__}")
        return None
