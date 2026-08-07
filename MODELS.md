# Models behind `data/ai-longform/`

What generated the released AI corpus, how precisely each model is pinned,
and where the pinning is weaker than it should be.

Added 2026-08-06 by the forensic code and data review (finding D-9). Every
row is read from `data/ai-longform/manifest.jsonl`, which records
`provider`, `model` (what was requested), `model_reported` (what the API or
runtime said it served), and `generated_at` per sample.

**All 1,072 samples were generated 2026-06-09 to 2026-06-11**, 134 per model,
by the repository owner.

## Pinning status per model

| Model (slug) | Provider | Requested | Served (`model_reported`) | Pinning |
|---|---|---|---|---|
| `gpt-5` | openai | `gpt-5` | **`gpt-5-2025-08-07`** | **dated snapshot recorded** |
| `gpt-5-mini` | openai | `gpt-5-mini` | **`gpt-5-mini-2025-08-07`** | **dated snapshot recorded** |
| `claude-haiku-4-5` | anthropic | `claude-haiku-4-5` | **`claude-haiku-4-5-20251001`** | **dated snapshot recorded** |
| `claude-fable-5` | anthropic | `claude-fable-5` | `claude-fable-5` | bare alias |
| `claude-opus-4-8` | anthropic | `claude-opus-4-8` | `claude-opus-4-8` | bare alias |
| `claude-sonnet-4-6` | anthropic | `claude-sonnet-4-6` | `claude-sonnet-4-6` | bare alias |
| `gemma4_26b` | ollama (local) | `gemma4:26b` | `gemma4:26b` | bare alias |
| `qwen3_6_35b` | ollama (local) | `qwen3.6:35b` | `qwen3.6:35b` | bare alias |

## The limitation, stated plainly

**Three of eight models are pinned to a dated snapshot. Five are not.**

- **Anthropic aliases (3 of 4).** For `claude-fable-5`, `claude-opus-4-8`,
  and `claude-sonnet-4-6` the API returned the alias rather than a dated
  snapshot id, and nothing at generation time resolved the alias to the
  underlying snapshot. Aliases move. If those aliases have since been
  repointed, the exact weights that produced these samples cannot now be
  identified from this record. `claude-haiku-4-5` shows what should have been
  captured for all four: the API returned `claude-haiku-4-5-20251001` and the
  manifest kept it.
- **Ollama local runs (2 of 2).** For `gemma4:26b` and `qwen3.6:35b`, the
  manifest records the Ollama tag only. **Neither the model digest (sha256)
  nor the quantization level was recorded at generation time**, and Ollama
  tags are mutable. Two people running `ollama run qwen3.6:35b` on different
  dates, or with different quantizations pulled, can be running measurably
  different models. This is the weakest pinning in the release.

Nothing recoverable now closes these gaps: the digests and snapshot ids were
not captured, and reconstructing them after the fact would be a guess. The
honest statement is that **five of the eight models are identified by a
mutable name plus a generation date, not by content.** For anyone rerunning
the generation, the sampling configuration is disclosed in the paper (§4.2)
and the per-sample `max_tokens`, `input_tokens`, `output_tokens`,
`stop_reason`, and `elapsed_seconds` are in the manifest.

What this does *not* affect: every number in the paper is computed from the
**released samples themselves**, which ship in full. The corpus is fixed and
checkable regardless of what the aliases point at today. The gap is in
*regenerating* comparable samples, not in verifying the published analysis.

## Output-rights basis per provider

The corpus is released CC0; the basis differs by provider, and is set out
per provider in `DATA_LICENSES.md` ("Why CC0 is ours to give, per
provider"). Summary: Anthropic and OpenAI both assign their rights in
outputs to the customer; Google claims no rights in Gemma outputs and
explicitly excludes outputs from "Model Derivatives"; Qwen3.6-35B-A3B is
Apache-2.0 with no separate output terms.

## Corpus composition

`data/ai-longform/sample_flags.json` (a sidecar; the manifest is not
modified) flags which records are refusal messages rather than fiction and
which fall below the paper's measurement floors. Regenerate it with
`python3 tools/flag_corpus_samples.py`.
