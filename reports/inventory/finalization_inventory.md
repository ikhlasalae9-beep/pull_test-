# Finalization inventory

The starting branch was `codex/work`; existing modified and untracked data/recovery work was preserved and included in final stabilization. No reset, history rewrite or retraining was performed.

| Category | Decision |
|---|---|
| Active website | Preserve Next.js `app/`, `components/`, `config/`, locale dictionaries and public brand/map assets |
| Final modeling | Preserve executed `ml/notebooks/maisondelux_notebook1.ipynb`, repaired CSV, fitted V1 object and metadata |
| Recovery notebooks | Preserve all three pipeline/scraping/repair notebooks: each orchestrates a distinct traceable stage, not a duplicate experiment |
| Collection/recovery source | Preserve legacy parser, recovery, validation, geography and V3 code: historical evidence and existing tests depend on it |
| Reports | Preserve data-quality, source audits and historical ML report; mark earlier model documentation as superseded |
| Superseded runtime | Remove four standalone HTML pages and three empty frontend asset placeholders; current site uses Next.js |
| Superseded model | Remove `ml/artifacts/pipeline.pkl`, `metrics.json`, `model_metadata.json`; no active inference/tests import these |
| Local generated products | Keep ignored recovery archives, raw/intermediate datasets and alternate exports needed for historical reproduction; do not add caches or experiments to Git |

Exact removed paths, pre-deletion sizes and SHA-256 hashes are in `removed_files.csv`. Historical inventory reports remain historical snapshots. The final dataset is explicitly exempted from `.gitignore` so a new checkout can run inference validation.

The notebook still contains its completed scientific comparisons and outputs: those form the evidence for model selection and are not obsolete experiments to discard. Its introductory stale counts were corrected and its custom transformer imports the identical reusable implementation for future exports.
