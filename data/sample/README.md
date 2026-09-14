# MaisonDeLUX modeling sample

`maisondelux_model_sample.csv` is a deterministic 750-row sample of
`data/processed/maisondelux_clean.parquet`. It contains only rows whose upstream
quality status is `valid` and whose deduplication status is `unique`; no values
were fabricated.

## Selection and coverage

- Fixed seed: `42`.
- City quotas are proportional to the full clean dataset, with a minimum of one
  row for every city.
- Within each city, selection is spread across price deciles, surface quintiles,
  and neighborhoods; less-represented neighborhoods are preferred as tie-breaks.
- Rows: 750; columns: 32; regions: 9; cities: 31; neighborhoods: 296.
- Price range: 150,000–34,000,000 MAD.
- Surface range: 29–1,288 m².
- Duplicate listing IDs: 0; duplicate non-empty URLs: 0.
- The header order exactly matches the canonical clean dataset.

The sample is suitable for schema checks, exploratory code, and fast pipeline
smoke tests. It is not a substitute for the full 13,867-row dataset when
estimating production metrics.

## Modeling columns

Target:

```text
price_mad
```

Safe candidate inputs include `region`, `city`, `neighborhood`, `surface_m2`,
`bedrooms`, `bathrooms`, `furnished_status`, `parking`, `balcony`, and
`sea_view`. The latitude/longitude columns are present for schema compatibility
but are entirely missing in the current clean corpus and should not be modeled.

Exclude identifiers, provenance, quality decisions, timestamps, and raw evidence
from the feature matrix. In particular, never use `price_per_m2` to predict
`price_mad`; it is calculated from the target and retained for audit only.

## Switching to the full data

Start quickly with:

```python
import pandas as pd
df = pd.read_csv("data/sample/maisondelux_model_sample.csv")
```

Then change only the loader for the full run:

```python
df = pd.read_parquet("data/processed/maisondelux_clean.parquet")
```

See `docs/ALAE_MODEL_TRAINING_HANDOFF.md` for split, feature, evaluation, and
backend-contract guidance.
