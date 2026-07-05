#!/usr/bin/env python3
"""Generate the AI long-form fiction corpus for author-space experiments E4+.

Produces matched long-form literary fiction samples (~3,500 words) across
Claude-family models (Anthropic API), OpenAI models, and local Ollama models,
under shared scenario prompts. Conditions (Tier 1 paper §4/§6/§10, issue #95
items P1 scale + P4/C3 prompt sensitivity — one matrix, one run):

- unprompted:      the scenario alone (the model's native literary voice),
                   10 scenarios.
- style_prompted:  the scenario plus "in the manner of <gold-shelf author>",
                   4 fixed (author, scenario) pairs.
- paraphrase:      3 alternate phrasings of the BASE instruction (same task,
                   different register: workshop prompt / editor brief / terse)
                   x a fixed subset of 4 scenarios, unprompted only. Tests
                   whether placement findings are robust to prompt wording.
- exemplar:        style_prompted PLUS two in-context excerpt passages
                   (~600 words each) of the target author, drawn from the
                   gold-shelf raw texts — the strongest imitation condition.
                   Same 4 (author, scenario) pairs as style_prompted.

RIGHTS NOTE (exemplar condition): the in-context excerpts are copyrighted
author text from locally-owned files. They are transmitted to the model API
solely for single-user research generation and are NEVER stored in the corpus
output or the manifest — the manifest records only the work titles, body
offsets, and excerpt positions used, so the condition is reproducible from
the local shelf without redistributing the text.

Repeated samples: models are stochastic at default settings, so repeated
calls are repeated samples. --samples-per-cell N generates N independent
samples per (model, condition, scenario[, target/paraphrase]) cell; the
sample index appears in the filename (<sample_id>__s<k>.txt) and manifest
(sample_index). Resume semantics are per (cell, index): existing files are
skipped. A legacy un-suffixed pilot file (<sample_id>.txt) counts as
sample index 1.

Outputs one .txt per sample under data/ai-longform/<model_slug>/ plus a
manifest JSONL recording full generation metadata. Samples are fully owned
(machine-generated here) — release-eligible without rights gating.

Comparability decisions (uniform across models):
- No sampling parameters (temperature/top_p removed on Fable 5 / Opus 4.8;
  omitted everywhere else for parity — provider defaults throughout).
- No extended/adaptive thinking on Claude (omitted — uniform "write
  directly" config). OpenAI gpt-5-family models reason by default; we leave
  the default in place (overriding it would itself be a config intervention)
  and record reasoning token counts in the manifest.
- Same prompts, same target length (~3,500 words), same condition matrix,
  max output tokens ~16,000 equivalent everywhere.
- Sequential calls within a model (rate-limit friendly); retry-once on
  transient API errors.

Relates: ADR-0041 (author-relative measurement space), experiments E4/C3,
TIER1_PAPER_OUTLINE.md §4/§6/§10, issue #95 (P1, P4).

Usage:
    # Claude family (needs ANTHROPIC_API_KEY) — main matrix, 5 samples/cell
    python tools/generate_ai_longform_corpus.py \
        --family claude --samples-per-cell 5 \
        --conditions unprompted,style_prompted,paraphrase,exemplar

    # OpenAI (needs OPENAI_API_KEY)
    python tools/generate_ai_longform_corpus.py \
        --family openai --samples-per-cell 5 \
        --conditions unprompted,style_prompted,paraphrase,exemplar

    # Local Ollama models (run when the machine is otherwise idle)
    python tools/generate_ai_longform_corpus.py \
        --family ollama --samples-per-cell 5 \
        --conditions unprompted,style_prompted,paraphrase,exemplar

    # One model, one condition, resumable (skips existing (cell, index))
    python tools/generate_ai_longform_corpus.py \
        --family claude --models claude-haiku-4-5 --conditions paraphrase
"""

from __future__ import annotations

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("generate_ai_longform_corpus")

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "data" / "raw" / "ai-longform"
AUTHOR_TEXT_ROOT = REPO_ROOT / "data" / "raw" / "author-data" / "text"
CONTROL_SHELF_MANIFEST = (
    REPO_ROOT / "data" / "baselines" / "author_space_build"
    / "control_shelf_manifest.yaml"
)

CLAUDE_MODELS = [
    "claude-fable-5",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
    "claude-haiku-4-5",
]
# Chosen by inspecting client.models.list() on this account (2026-06-09):
# available = gpt-4, gpt-4.1, gpt-4o, gpt-4o-mini, gpt-5, gpt-5-mini,
# gpt-5-nano, gpt-5-pro. Flagship general model = gpt-5 (gpt-5-pro is the
# heavy deliberate-reasoning tier — wrong cost/latency profile for a matched
# corpus); mini tier = gpt-5-mini.
OPENAI_MODELS = [
    "gpt-5",
    "gpt-5-mini",
]
OLLAMA_MODELS = [
    "gemma4:26b",
    "qwen3.6:35b",
]

TARGET_WORDS = 3500
MAX_TOKENS = 16000  # streaming; ~3.5k words needs ~5k tokens, leave headroom

ALL_CONDITIONS = ["unprompted", "style_prompted", "paraphrase", "exemplar"]
DEFAULT_CONDITIONS = "unprompted,style_prompted"

# Ten shared scenarios spanning common literary-fiction modes. Deliberately
# adjacent to gold-shelf territory (grief, landscape, memory, labor) so that
# placement against the author manifold is interpretable. The first six are
# the v0 pilot scenarios (unchanged for comparability); the last four are
# the P1 scale-up additions.
SCENARIOS = {
    "estate_sale": (
        "A woman in her fifties spends a single afternoon managing the estate "
        "sale of her late mother's house in a small Ohio town, while strangers "
        "carry the furniture of her childhood out the front door."
    ),
    "night_ferry": (
        "A man crosses a northern strait on an overnight ferry to identify a "
        "body that may or may not be his estranged brother's."
    ),
    "irrigation": (
        "Two brothers spend a June day repairing an irrigation line on the "
        "failing family orchard, arguing about whether to sell the land."
    ),
    "harbor_winter": (
        "A retired harbor pilot in a fading fishing town teaches his "
        "granddaughter to read the water during the last winter the cannery "
        "is open."
    ),
    "hotel_fire": (
        "Years after a hotel fire she survived as a chambermaid, a woman "
        "returns to the rebuilt hotel as a wedding guest."
    ),
    "wire_voices": (
        "A long-distance telephone operator in 1968 becomes attached to two "
        "voices whose weekly calls she connects, until one week only one of "
        "them calls."
    ),
    # --- P1 scale-up scenarios (added 2026-06) ---
    "drowned_town": (
        "After a drought drops the reservoir to its lowest level in sixty "
        "years, a county surveyor returns to map the exposed streets of the "
        "drowned town where she was born, walking foundations she last saw "
        "above water as a child."
    ),
    "lambing_storm": (
        "A widowed sheep farmer and her teenage son work through a late-April "
        "blizzard in the lambing shed, their first season without her "
        "husband, while the storm takes the power and the ewes keep coming."
    ),
    "fire_lookout": (
        "A woman serving her final summer in a decommissioned fire lookout "
        "tower watches a smoke column rise from the drainage where her "
        "estranged sister keeps a cabin, with the radio dead and the road "
        "eight miles downhill."
    ),
    "piano_tuner": (
        "An elderly piano tuner makes the last round of his rural route, "
        "tuning instruments nobody plays anymore, ending at the church where "
        "his son gave his first and only recital."
    ),
}

# Style-prompted condition targets — gold-shelf authors with distinct,
# well-known styles. Each is paired with one scenario (fixed pairing so every
# model gets the identical task). The exemplar condition reuses these pairs.
STYLE_TARGETS = [
    ("mccarthy-cormac", "Cormac McCarthy", "irrigation"),
    ("didion-joan", "Joan Didion", "hotel_fire"),
    ("ondaatje-michael", "Michael Ondaatje", "night_ferry"),
    ("morrison-toni", "Toni Morrison", "estate_sale"),
]

# Paraphrase condition runs on a fixed subset of 4 scenarios — the same four
# scenarios used by the style/exemplar pairs, so prompt-sensitivity variance
# is measured exactly where the imitation conditions live.
PARAPHRASE_SCENARIOS = ["irrigation", "hotel_fire", "night_ferry", "estate_sale"]

BASE_INSTRUCTION = (
    "Write a self-contained literary fiction excerpt of approximately "
    f"{TARGET_WORDS} words based on the following premise. Write continuous "
    "narrative prose — no chapter headings, no scene-break markers, no title, "
    "no authorial commentary before or after. Begin directly with the prose "
    "and end when the excerpt feels complete.\n\nPremise: {premise}"
)

STYLE_INSTRUCTION = (
    "Write a self-contained literary fiction excerpt of approximately "
    f"{TARGET_WORDS} words based on the following premise, in the manner of "
    "{author}. Inhabit the style fully — diction, rhythm, syntax, structure "
    "— rather than imitating surface tics. Write continuous narrative prose "
    "— no chapter headings, no scene-break markers, no title, no authorial "
    "commentary before or after. Begin directly with the prose and end when "
    "the excerpt feels complete.\n\nPremise: {premise}"
)

# Three alternate phrasings of the BASE instruction (P4/C3 prompt
# sensitivity). Same task — ~3,500 words of continuous literary prose from
# the premise, no title/headings/commentary — in three different registers.
PARAPHRASE_INSTRUCTIONS = {
    "workshop": (
        "Here is a writing-workshop prompt: {premise}\n\n"
        "Write the piece in full — literary fiction, somewhere around "
        f"{TARGET_WORDS} words of finished prose. Give us the prose and "
        "nothing else: no title, no chapter headings, no asterisked scene "
        "breaks, and no notes about your choices before or after. Start "
        "inside the story and stop when it has earned its ending."
    ),
    "editor_brief": (
        "BRIEF: We need a self-contained excerpt of literary fiction, c. "
        f"{TARGET_WORDS} words, developed from the premise below. The "
        "deliverable is continuous narrative prose only — no front matter, "
        "no title, no section markers, and no commentary of any kind "
        "preceding or following the text. The excerpt should open in the "
        "fiction itself and close at a natural resting point.\n\n"
        "Premise: {premise}"
    ),
    "terse": (
        f"Literary fiction, ~{TARGET_WORDS} words, from this premise: "
        "{premise}\n\n"
        "Prose only, one continuous narrative. No title, no headings, no "
        "scene-break markers, no commentary. Begin with the first sentence "
        "of the story and end where it ends."
    ),
}

# Exemplar condition (P4/C3): style_prompted plus two in-context passages of
# the target author. See RIGHTS NOTE in the module docstring — excerpt text
# is sent to the API only and never written to corpus output or manifest.
EXEMPLAR_SEED = 20260609
EXEMPLAR_WORDS = 600
EXEMPLAR_POSITIONS = (0.25, 0.60)  # fraction through the work's body text

# Works excluded from exemplar selection: formally atypical of the author's
# narrative prose (Stella Maris is a Q&A interview transcript), so a passage
# would be an unrepresentative voice exemplar.
EXEMPLAR_EXCLUDE_TITLES = {
    "mccarthy-cormac": {"Stella Maris"},
}

EXEMPLAR_INSTRUCTION = (
    "Here are two passages by {author}:\n\n"
    "<passage 1>\n{excerpt_1}\n</passage 1>\n\n"
    "<passage 2>\n{excerpt_2}\n</passage 2>\n\n"
    "Write a self-contained literary fiction excerpt of approximately "
    f"{TARGET_WORDS} words based on the following premise, in the manner of "
    "{author}, matching the voice of these passages. Inhabit the style fully "
    "— diction, rhythm, syntax, structure — rather than imitating surface "
    "tics. Write continuous narrative prose — no chapter headings, no "
    "scene-break markers, no title, no authorial commentary before or after. "
    "Begin directly with the prose and end when the excerpt feels "
    "complete.\n\nPremise: {premise}"
)


def _load_control_shelf_works() -> list[dict]:
    import yaml

    with open(CONTROL_SHELF_MANIFEST, encoding="utf-8") as fh:
        manifest = yaml.safe_load(fh)
    return manifest["works"]


def _excerpt_from_work(work: dict, fraction: float) -> tuple[str, dict]:
    """Pull ~EXEMPLAR_WORDS words starting ~fraction through the work body.

    Snaps the start forward to a sentence boundary. Returns (excerpt_text,
    provenance_meta). The text goes into the prompt only; the meta (no text)
    goes into the manifest.
    """
    raw = (AUTHOR_TEXT_ROOT / work["file_path"]).read_text(
        encoding="utf-8", errors="replace"
    )
    body = raw[work["body_start_offset"]:work["body_end_offset"]]
    words = body.split()
    start = int(len(words) * fraction)
    # Snap forward to the word after a sentence terminator (bounded search).
    limit = min(start + 400, len(words) - EXEMPLAR_WORDS)
    snapped = start
    while snapped < limit and not words[snapped - 1].rstrip("'\"”’)").endswith(
        (".", "!", "?")
    ):
        snapped += 1
    if snapped < limit:
        start = snapped
    excerpt = " ".join(words[start:start + EXEMPLAR_WORDS])
    meta = {
        "title": work["title"],
        "file_path": work["file_path"],
        "body_start_offset": work["body_start_offset"],
        "body_end_offset": work["body_end_offset"],
        "excerpt_fraction": fraction,
        "excerpt_start_word": start,
        "excerpt_word_count": len(excerpt.split()),
    }
    return excerpt, meta


def load_exemplar_excerpts(author_slug: str) -> tuple[list[str], list[dict]]:
    """Deterministically pick 2 clean novels by the author and excerpt them.

    Selection is seeded (EXEMPLAR_SEED) over the file-path-sorted list of
    clean novels in the control-shelf manifest, so every run (and every
    model) sees the identical passages.
    """
    excluded = EXEMPLAR_EXCLUDE_TITLES.get(author_slug, set())
    works = [
        w for w in _load_control_shelf_works()
        if w["author_slug"] == author_slug
        and w["form"] == "novel"
        and w["fidelity_verdict"] == "clean"
        and w["title"] not in excluded
    ]
    if len(works) < 2:
        raise RuntimeError(
            f"Need >=2 clean novels for exemplar target {author_slug}, "
            f"found {len(works)}"
        )
    works.sort(key=lambda w: w["file_path"])
    rng = random.Random(f"{EXEMPLAR_SEED}:{author_slug}")
    chosen = rng.sample(works, 2)
    excerpts, metas = [], []
    for work, fraction in zip(chosen, EXEMPLAR_POSITIONS):
        excerpt, meta = _excerpt_from_work(work, fraction)
        excerpts.append(excerpt)
        metas.append(meta)
    return excerpts, metas


def build_sample_plan(conditions: list[str]) -> list[dict]:
    """The per-model cell matrix for the requested conditions.

    Cell counts: unprompted 10, style_prompted 4, paraphrase 3x4=12,
    exemplar 4 (total 30 with all conditions). Multiply by --samples-per-cell
    for sample counts.
    """
    plan = []
    if "unprompted" in conditions:
        for scenario_id, premise in SCENARIOS.items():
            plan.append(
                {
                    "sample_id": f"{scenario_id}__unprompted",
                    "scenario_id": scenario_id,
                    "condition": "unprompted",
                    "style_target": None,
                    "paraphrase_id": None,
                    "exemplar_works": None,
                    "prompt": BASE_INSTRUCTION.format(premise=premise),
                }
            )
    if "style_prompted" in conditions:
        for author_slug, author_name, scenario_id in STYLE_TARGETS:
            plan.append(
                {
                    "sample_id": f"{scenario_id}__style_{author_slug}",
                    "scenario_id": scenario_id,
                    "condition": "style_prompted",
                    "style_target": author_slug,
                    "paraphrase_id": None,
                    "exemplar_works": None,
                    "prompt": STYLE_INSTRUCTION.format(
                        author=author_name, premise=SCENARIOS[scenario_id]
                    ),
                }
            )
    if "paraphrase" in conditions:
        for paraphrase_id, template in PARAPHRASE_INSTRUCTIONS.items():
            for scenario_id in PARAPHRASE_SCENARIOS:
                plan.append(
                    {
                        "sample_id": f"{scenario_id}__para_{paraphrase_id}",
                        "scenario_id": scenario_id,
                        "condition": "paraphrase",
                        "style_target": None,
                        "paraphrase_id": paraphrase_id,
                        "exemplar_works": None,
                        "prompt": template.format(
                            premise=SCENARIOS[scenario_id]
                        ),
                    }
                )
    if "exemplar" in conditions:
        for author_slug, author_name, scenario_id in STYLE_TARGETS:
            excerpts, metas = load_exemplar_excerpts(author_slug)
            logger.info(
                "Exemplar %s: %s (%d words @ %.0f%%), %s (%d words @ %.0f%%)",
                author_slug,
                metas[0]["title"], metas[0]["excerpt_word_count"],
                metas[0]["excerpt_fraction"] * 100,
                metas[1]["title"], metas[1]["excerpt_word_count"],
                metas[1]["excerpt_fraction"] * 100,
            )
            plan.append(
                {
                    "sample_id": f"{scenario_id}__exemplar_{author_slug}",
                    "scenario_id": scenario_id,
                    "condition": "exemplar",
                    "style_target": author_slug,
                    "paraphrase_id": None,
                    # Provenance only — never the excerpt text itself.
                    "exemplar_works": metas,
                    "prompt": EXEMPLAR_INSTRUCTION.format(
                        author=author_name,
                        excerpt_1=excerpts[0],
                        excerpt_2=excerpts[1],
                        premise=SCENARIOS[scenario_id],
                    ),
                }
            )
    return plan


def model_slug(model: str) -> str:
    return model.replace(":", "_").replace("/", "_").replace(".", "_")


def generate_claude(model: str, prompt: str) -> tuple[str, dict]:
    import anthropic

    client = anthropic.Anthropic()
    # Streaming guards against HTTP timeouts on long outputs. No thinking
    # param (uniform config; Fable 5 rejects explicit disabled), no sampling
    # params (removed on Fable 5 / Opus 4.8).
    with client.messages.stream(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        message = stream.get_final_message()
    text = "".join(b.text for b in message.content if b.type == "text")
    meta = {
        "provider": "anthropic",
        "model_reported": message.model,
        "stop_reason": message.stop_reason,
        "output_tokens": message.usage.output_tokens,
        "input_tokens": message.usage.input_tokens,
    }
    return text, meta


def generate_openai(model: str, prompt: str) -> tuple[str, dict]:
    from openai import OpenAI

    client = OpenAI()
    # Responses API (openai SDK 2.x). Streaming guards against HTTP timeouts
    # on long outputs. No temperature/top_p (provider defaults for parity);
    # gpt-5-family reasoning is left at its default and the reasoning token
    # count is recorded.
    with client.responses.stream(
        model=model,
        input=prompt,
        max_output_tokens=MAX_TOKENS,
    ) as stream:
        response = stream.get_final_response()
    text = response.output_text
    usage = response.usage
    details = getattr(usage, "output_tokens_details", None)
    stop_reason = response.status
    if response.status == "incomplete" and response.incomplete_details:
        stop_reason = f"incomplete:{response.incomplete_details.reason}"
    meta = {
        "provider": "openai",
        "model_reported": response.model,
        "stop_reason": stop_reason,
        "output_tokens": usage.output_tokens if usage else None,
        "input_tokens": usage.input_tokens if usage else None,
        "reasoning_tokens": (
            details.reasoning_tokens if details is not None else None
        ),
    }
    return text, meta


def generate_ollama(model: str, prompt: str, host: str) -> tuple[str, dict]:
    import urllib.request

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": MAX_TOKENS},
    }
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=3600) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = data.get("message", {}).get("content", "")
    meta = {
        "provider": "ollama",
        "model_reported": data.get("model", model),
        "stop_reason": data.get("done_reason"),
        "output_tokens": data.get("eval_count"),
        "input_tokens": data.get("prompt_eval_count"),
    }
    return text, meta


_TRANSIENT_MARKERS = (
    "overloaded", "rate limit", "rate_limit", "too many requests",
    "timeout", "timed out", "connection", "temporarily", "server error",
    "service unavailable", "bad gateway",
)


def is_transient(exc: Exception) -> bool:
    """Heuristic: retry-once-worthy API errors (429/5xx/408, network)."""
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code in (408, 409, 429) or code >= 500
    msg = str(exc).lower()
    return any(marker in msg for marker in _TRANSIENT_MARKERS)


def generate_with_retry(family: str, model: str, prompt: str,
                        ollama_host: str) -> tuple[str, dict]:
    """One generation, retrying once on transient API errors."""
    for attempt in (1, 2):
        try:
            if family == "claude":
                return generate_claude(model, prompt)
            if family == "openai":
                return generate_openai(model, prompt)
            return generate_ollama(model, prompt, ollama_host)
        except Exception as exc:
            if attempt == 1 and is_transient(exc):
                logger.warning(
                    "Transient error (%s) — retrying once in 20s", exc
                )
                time.sleep(20)
                continue
            raise
    raise AssertionError("unreachable")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate AI long-form fiction corpus (experiments E4/C3)"
    )
    parser.add_argument(
        "--family", choices=["claude", "openai", "ollama"], required=True,
        help="Which model family to generate with",
    )
    parser.add_argument(
        "--models", type=str, default=None,
        help="Comma-separated model list (default: family defaults)",
    )
    parser.add_argument(
        "--conditions", type=str, default=DEFAULT_CONDITIONS,
        help=(
            "Comma-separated conditions to generate "
            f"(choices: {','.join(ALL_CONDITIONS)}; "
            f"default: {DEFAULT_CONDITIONS})"
        ),
    )
    parser.add_argument(
        "--samples-per-cell", type=int, default=1,
        help="Independent samples per (model, condition, cell) (default 1)",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Stop after generating this many new samples (smoke testing)",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR,
        help=f"Output root (default {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--ollama-host", type=str, default="http://127.0.0.1:11434",
        help="Ollama API host",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    bad = [c for c in conditions if c not in ALL_CONDITIONS]
    if bad:
        parser.error(f"Unknown condition(s): {', '.join(bad)}")
    if args.samples_per_cell < 1:
        parser.error("--samples-per-cell must be >= 1")

    if args.models:
        models = [m.strip() for m in args.models.split(",") if m.strip()]
    else:
        models = {
            "claude": CLAUDE_MODELS,
            "openai": OPENAI_MODELS,
            "ollama": OLLAMA_MODELS,
        }[args.family]

    plan = build_sample_plan(conditions)
    manifest_path = args.output_dir / "manifest.jsonl"
    args.output_dir.mkdir(parents=True, exist_ok=True)

    total = len(models) * len(plan) * args.samples_per_cell
    done = failed = skipped = 0

    jobs = (
        (model, sample, sample_index)
        for model in models
        for sample in plan
        for sample_index in range(1, args.samples_per_cell + 1)
    )
    for model, sample, sample_index in jobs:
        if args.limit is not None and done + failed >= args.limit:
            logger.info("Reached --limit %d, stopping.", args.limit)
            break
        slug = model_slug(model)
        model_dir = args.output_dir / slug
        model_dir.mkdir(parents=True, exist_ok=True)
        out_path = model_dir / f"{sample['sample_id']}__s{sample_index}.txt"
        legacy_path = model_dir / f"{sample['sample_id']}.txt"
        if out_path.exists() or (sample_index == 1 and legacy_path.exists()):
            skipped += 1
            continue
        label = f"{model} / {sample['sample_id']} / s{sample_index}"
        logger.info("Generating %s ...", label)
        start = time.time()
        try:
            text, meta = generate_with_retry(
                args.family, model, sample["prompt"], args.ollama_host
            )
        except Exception as exc:  # keep the run going; record the failure
            logger.error("FAILED %s: %s", label, exc)
            failed += 1
            continue
        elapsed = time.time() - start
        word_count = len(text.split())
        if word_count < 800:
            logger.warning(
                "%s produced only %d words — keeping but flagging",
                label, word_count,
            )
        out_path.write_text(text, encoding="utf-8")
        record = {
            "sample_id": sample["sample_id"],
            "sample_index": sample_index,
            "model": model,
            "model_slug": slug,
            "file_path": str(out_path.relative_to(args.output_dir)),
            "scenario_id": sample["scenario_id"],
            "condition": sample["condition"],
            "style_target": sample["style_target"],
            "paraphrase_id": sample["paraphrase_id"],
            "exemplar_works": sample["exemplar_works"],
            "word_count": word_count,
            "elapsed_seconds": round(elapsed, 1),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target_words": TARGET_WORDS,
            "max_tokens": MAX_TOKENS,
            **meta,
        }
        with open(manifest_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        done += 1
        logger.info(
            "  done: %d words in %.0fs (%d/%d complete)",
            word_count, elapsed, done + skipped, total,
        )

    logger.info(
        "Finished: %d generated, %d skipped (existing), %d failed, %d total",
        done, skipped, failed, total,
    )
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
