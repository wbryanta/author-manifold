# P6 — Model Self-Consistency (are LLMs narrow-variance authors?)

- Generated: 2026-06-11T00:32:02.321217+00:00; artifact: wave-2 (15-author)
- Human reference: within-author pairs p50 0.740 (p90 1.084); between-author pairs p50 1.076

| Model | n | within-model Δ p50 | vs human within p50 |
|---|---|---|---|
| claude-fable-5 | 50 | 1.633 | 2.21x |
| claude-haiku-4-5 | 50 | 1.855 | 2.51x |
| claude-opus-4-8 | 50 | 1.830 | 2.47x |
| claude-sonnet-4-6 | 50 | 1.708 | 2.31x |
| gemma4:26b | 50 | 1.548 | 2.09x |
| gpt-5 | 50 | 1.373 | 1.86x |
| gpt-5-mini | 50 | 1.404 | 1.90x |
| qwen3.6:35b | 50 | 1.801 | 2.43x |

LOO self-attribution: **97.8%** over 400 trials, 8 models (chance 12.5%).

Cross-model centroid Delta (sorted):

- claude-fable-5|claude-opus-4-8: 0.549
- claude-haiku-4-5|claude-sonnet-4-6: 0.609
- claude-opus-4-8|claude-sonnet-4-6: 0.791
- gpt-5|gpt-5-mini: 0.803
- claude-fable-5|claude-sonnet-4-6: 0.822
- claude-opus-4-8|gpt-5: 0.914
- claude-haiku-4-5|claude-opus-4-8: 0.929
- gemma4:26b|qwen3.6:35b: 0.955
- claude-fable-5|gpt-5: 0.960
- claude-haiku-4-5|gpt-5-mini: 0.992
- claude-fable-5|claude-haiku-4-5: 1.004
- claude-haiku-4-5|qwen3.6:35b: 1.024
- claude-fable-5|qwen3.6:35b: 1.046
- claude-sonnet-4-6|qwen3.6:35b: 1.046
- claude-sonnet-4-6|gpt-5-mini: 1.051
- claude-opus-4-8|qwen3.6:35b: 1.055
- claude-sonnet-4-6|gpt-5: 1.070
- claude-haiku-4-5|gpt-5: 1.098
- claude-opus-4-8|gpt-5-mini: 1.122
- gpt-5-mini|qwen3.6:35b: 1.161
- gpt-5|qwen3.6:35b: 1.167
- claude-fable-5|gpt-5-mini: 1.189
- claude-haiku-4-5|gemma4:26b: 1.231
- claude-sonnet-4-6|gemma4:26b: 1.292
- gemma4:26b|gpt-5-mini: 1.307
- claude-opus-4-8|gemma4:26b: 1.393
- claude-fable-5|gemma4:26b: 1.420
- gemma4:26b|gpt-5: 1.482
