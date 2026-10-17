# Drug Review Explorer

Dimensional aspect-based sentiment analysis of patient drug reviews. A Streamlit app with four pages:

| Page | What it shows | Data |
|---|---|---|
| Drugs | Effectiveness breakdown, side effects with typical severity, patient quotes, stars-vs-text mismatches | Precomputed predictions on Drugs.com |
| Review detail | One review with aspect spans, labels, optional valence/arousal scores, and a six-model comparison | Precomputed predictions |
| Try a review | Live scoring of any typed review | Runs the selected model live |
| Model check | Druglib test reviews: model scores next to patient ratings, RMSE and MAE per model | Druglib test split |

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

It works immediately on **generated demo data** (a yellow banner says so on every page). Nothing below is a real result until you plug in your models and data.

## Project layout

```
app.py                  navigation (four pages)
views/                  one file per page
core/registry.py        MODEL REGISTRY: the six encoders, their checkpoints, the scorer
core/aspects.py         finds which aspects a review mentions (lexicon stand-in for a DimASTE extractor)
core/labels.py          valence/arousal -> words ("Worked well", "Severe"); thresholds live here
core/data.py            data loading, batch scoring, per-drug summaries, Druglib evaluation
core/ui.py              Streamlit caching and shared display helpers
scripts/batch_score.py  scores all Drugs.com reviews with all models -> data/predictions.parquet
.streamlit/config.toml  colors matching the design prototype
```

## Going from demo data to real results

1. **Train in Colab.** Fine-tune each encoder with a 2-output regression head (valence, arousal), input as a sentence pair `(review text, aspect)`, MSE loss. Stage 1 on DimABSA English data, stage 2 on Druglib with ordinal labels mapped to VA targets.
2. **Push checkpoints to the Hugging Face Hub**: `model.push_to_hub("your-team/drugreview-deberta", private=True)` and the same for the tokenizer.
3. **Fill in `ckpt`** for each model in `core/registry.py`. Once any `ckpt` is set, the fake scorer switches off for that model and the banner disappears when all are set. Uncomment `torch` and `transformers` in `requirements.txt`.
4. **Batch-score Drugs.com** in Colab:
   `python scripts/batch_score.py drugsComTrain_raw.tsv drugsComTest_raw.tsv`
   This writes `data/predictions.parquet`, which the app loads automatically.
5. **Replace the Druglib demo reviews** in `core/data.py` (`_DRUGLIB_TEST`) with the real Druglib test split. The model check page and its RMSE/MAE table then report your real results.
6. **Calibrate the label thresholds** in `core/labels.py` against Druglib's categorical labels and report the values in the paper.

## Notes

- `@st.cache_resource` loads each model once. Only the live demo page runs a model; the other pages read precomputed predictions.
- Six models will not all fit in GPU memory at once. In deployment, keep one or two available for the live demo.
- Keep `data/predictions.parquet` out of public repos. It contains Drugs.com review text, and the dataset terms say not to redistribute it.
- Deploy on Hugging Face Spaces (Streamlit) or Streamlit Community Cloud.
