# P4 — Prompt-Wording Sensitivity (paraphrase condition)

- Generated: 2026-06-11T00:32:03.988500+00:00; scenarios: estate_sale, hotel_fire, irrigation, night_ferry

| Phrasing | n | median nearest dist | off-manifold rate |
|---|---|---|---|
| base | 160 | 1.625 | 1.000 |
| workshop | 64 | 1.619 | 1.000 |
| editor_brief | 60 | 1.591 | 1.000 |
| terse | 62 | 1.593 | 1.000 |

Per-model max spread across phrasing medians:

- claude-fable-5: 0.033
- claude-haiku-4-5: 0.078
- claude-opus-4-8: 0.100
- claude-sonnet-4-6: 0.075
- gemma4:26b: 0.093
- gpt-5: 0.019
- gpt-5-mini: 0.064
- qwen3.6:35b: 0.106
