# Reliability scoring

Score range: 0–100

```
score = clamp(
  0.35 * source_trust
+ 0.25 * confirmation_count
+ 0.20 * feedback_sentiment
+ 0.10 * historical_accuracy
+ 0.10 * freshness
- cancellation_penalty
, 0, 100)
```

## Source trust weights

| Source | Weight |
|---|---|
| website | 80 |
| reddit | 60 |
| facebook | 55 |
| instagram | 50 |
| forum | 40 |
| user_submission | 45 |

## Labels (Swedish)

| Score | Label |
|---|---|
| cancelled | Inställd |
| >= 70 | Pålitlig |
| >= 40 | Osäker |
| < 40 | Overifierad |

Recomputed nightly via `worker.tasks.recompute_all_scores` and on new feedback.
