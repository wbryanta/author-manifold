# K8 — Completion Condition Placement (LM envelopes)

- Generated: 2026-06-11T08:06:40.225669+00:00; primary vocab: fw-only
- 160 generations recorded: 87 compliant (>= 3000 tokens), 35 sub-floor, 38 refused/partial (< 1500, incl. 1 zero-length output(s) counted as refused/partial)

## Compliance per model

| Model | compliant | sub-floor | refused/partial |
|---|---|---|---|
| claude-fable-5 | 20 | 0 | 0 |
| claude-haiku-4-5 | 2 | 18 | 0 |
| claude-opus-4-8 | 20 | 0 | 0 |
| claude-sonnet-4-6 | 20 | 0 | 0 |
| gemma4:26b | 1 | 14 | 5 |
| gpt-5 | 0 | 0 | 20 |
| gpt-5-mini | 8 | 0 | 12 |
| qwen3.6:35b | 16 | 3 | 1 |

Zero-length outputs (in refused/partial): `qwen3_6_35b/completion_mccarthy-cormac__s3.txt`

## Entry — fwonly vocabulary (PRIMARY)

Pooled: 27/87 = 31.0% @p90 (CP [21.5%, 41.9%]); p95 32, p99 55
Clustering ((model x target) cells, 21 cells): ICC 0.570, DEFF 2.79, n_eff 31; DEFF-adj CP [15.8%, 50.1%]; cell-bootstrap [14.3%, 48.1%]

| Model | n | entered p90 | p95 | p99 |
|---|---|---|---|---|
| claude-fable-5 | 20 | 10 | 11 | 16 |
| claude-haiku-4-5 | 2 | 0 | 0 | 1 |
| claude-opus-4-8 | 20 | 7 | 7 | 10 |
| claude-sonnet-4-6 | 20 | 3 | 4 | 10 |
| gemma4:26b | 1 | 0 | 1 | 1 |
| gpt-5-mini | 8 | 5 | 6 | 7 |
| qwen3.6:35b | 16 | 2 | 3 | 10 |

| Target | n | entered p90 |
|---|---|---|
| didion-joan | 24 | 3 |
| mccarthy-cormac | 25 | 19 |
| morrison-toni | 18 | 4 |
| ondaatje-michael | 20 | 1 |

## Entry — full vocabulary (content-confounded secondary)

Pooled: 18/87 = 20.7% @p90 (CP [12.7%, 30.7%]); p95 29, p99 55
Clustering ((model x target) cells, 21 cells): ICC 0.753, DEFF 3.37, n_eff 26; DEFF-adj CP [7.4%, 41.1%]; cell-bootstrap [5.5%, 37.2%]

| Model | n | entered p90 | p95 | p99 |
|---|---|---|---|---|
| claude-fable-5 | 20 | 10 | 14 | 20 |
| claude-haiku-4-5 | 2 | 0 | 0 | 0 |
| claude-opus-4-8 | 20 | 3 | 5 | 12 |
| claude-sonnet-4-6 | 20 | 5 | 5 | 12 |
| gemma4:26b | 1 | 0 | 0 | 1 |
| gpt-5-mini | 8 | 0 | 5 | 5 |
| qwen3.6:35b | 16 | 0 | 0 | 5 |

| Target | n | entered p90 |
|---|---|---|
| didion-joan | 24 | 4 |
| mccarthy-cormac | 25 | 13 |
| morrison-toni | 18 | 0 |
| ondaatje-michael | 20 | 1 |
