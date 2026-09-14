# Recovered legacy Scrapy adapter

This package was recovered from interrupted uncommitted work and is retained for offline parser, checkpoint, retry, and rate-limit tests.

**Live Mubawab collection is disabled.** Its public pages may be allowed by robots rules, but the current site conditions restrict substantial extraction/reuse and extraction software. Do not run `ml/scraping/run.py` without written permission and an authorization record in the source policy.

Use the active policy-gated architecture instead:

```bash
python -m ml.src.scraping.pilot
```

If written permission is later obtained, the legacy implementation already provides JSON-LD-first parsing, one-request-at-a-time throttling, exponential retry for transient failures, persistent 429 cooldowns, append-and-flush CSV checkpointing, native-ID/canonical-URL resume, and structured failure logs. Re-run its bounded 4-listing pilot and manually verify every field before increasing limits.
