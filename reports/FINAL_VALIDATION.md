# Final validation — 2026-09-05

- Branch verified: `codex/work`.
- Existing local changes preserved; no retraining, reset, merge or history rewrite.
- `python -m pytest -q -p no:cacheprovider --basetemp=outputs/final-pytest-3`: **63 passed**.
- `npm run build`: **passed**, including TypeScript and lint checks; French and Arabic estimation pages plus `/api/estimate` produced.
- All four notebooks parse and validate with nbformat.
- Portable serialization preserves every prediction on the 13,537-row dataset exactly.
- Regression test recreates the 2,685-row group-aware Test split, matches official MAE/R², verifies 237 preprocessing columns, and verifies inverse-log output.
- API examples for Casablanca, Rabat, Marrakech and Tanger return finite positive MAD prices.
- Unknown neighborhood, missing numeric values and omitted/null amenities pass; invalid/nonfinite surface and undeclared target-derived fields are rejected.
- Model-output failure returns a controlled 503.
- Browser test against the production build on port 3001: Casablanca / Maârif / 120 m² / 3 bedrooms / 2 bathrooms / amenities unknown returned **1,864,492 MAD**.
- Loading state observed before prediction. Flask stopped: frontend displayed service-unavailable state without price. Flask restarted: retry returned the same real prediction.
- Privacy scan of 166 tracked/nonignored project files (including notebook JSON and binary bytes interpreted as UTF-8/UTF-16): **zero matches**. A personal reference in an ignored generated geography-detail report was also removed. Git history and external dependency caches were not rewritten.
- `git diff --check`: passed. The ten removed paths and their pre-removal hashes are recorded in `reports/inventory/removed_files.csv`.

Local environment notes: the first full pytest attempt hit an existing Windows temporary-directory permission issue; a project-local `--basetemp` resolved it. Port 3000 was occupied by a pre-existing process, so production-browser QA used port 3001. Neither issue changes the application defaults.

## Remaining limitations

The prototype uses asking prices from a single main historical source, imbalanced coverage and mostly apartments. Missing traceability, dates, coordinates and amenities limit generalization. Sensitivity R² ≈0.77 is not official Test performance. No calibrated confidence interval is served. Full historical recovery needs ignored local archives/geographic exports; inference and its regression tests use versioned assets. Flask's development server is suitable for local demonstration; deployment needs an appropriate production server.
