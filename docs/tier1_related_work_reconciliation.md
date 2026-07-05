# Tier 1 Paper — Related-Work Reconciliation (P9 sweep, 2026-06-09)

Scope: positions the three Tier 1 claims against the 2024-2026 literature
(plus load-bearing older anchors). Companion YAML summaries live in
`docs/research/papers/` (15 new entries, this sweep). Claims as in
`TIER1_PAPER_OUTLINE.md` §5:

- **C-A (R1):** unprompted frontier-model long-form fiction sits beyond
  ~p98 of calibrated within-author (W) variation, for every shelf author.
- **C-B (R2):** style prompting moves samples *toward* the target author
  (nearest-neighbor hits) but never *into* the target's W region at the
  function-word level (0/16 in outline v0.1; current corpus 0/24 across
  three model families, ~3,500-word samples).
- **C-C (frame):** within/between-author percentile calibration as the
  measurement unit, instead of detector/classifier scores.

---

## 1. The contrast class: papers claiming (or read as claiming) successful imitation

### 1.1 Jones, Nurse & Li 2022 — "Are You Robert or RoBERTa?" (ICWSM)

**Their claim:** GPT-2 generators conditioned on a target user's posts
produce text that "successfully mimic[s] authorship," deceiving online
authorship-attribution models on blog and Twitter data.

**How it differs from us:**
- **Length:** tweets and blog posts — tens to a few hundred words. Our E6
  shows exactly why this regime is permissive: attribution collapses with
  length (B/W separation 1.61 → 1.06 from full work to 800 words; LOO
  94.9% → 56.3%). Deceiving attribution where the signal barely exists is
  a different claim from entering an author's region at 3,500 words.
- **Success criterion:** fooling *specific trained classifiers* (a
  decision boundary), not closing a calibrated distance. A classifier can
  be wrong while the text remains far from the target in Delta space.
- **Generator:** fine-tuned/conditioned GPT-2 on the target's own text —
  closer to text completion than to instruction-prompted style transfer.

**What we must say:** short-text classifier-deception results do not bear
on long-form calibrated placement; we should state the length-regime
argument explicitly (with our E6 numbers) and note the criterion
difference (decision flip vs region entry). Do not claim they are wrong —
both results can be true simultaneously.

### 1.2 Jemama & Kumar 2025 — "How Well Do LLMs Imitate Human Writing Style?" (IEEE UEMCON; arXiv:2509.24930)

**Their claim:** the strongest recent imitation-succeeds headline:
text-completion prompting reaches **99.9% agreement with the original
author's style**; few-shot gives up to 23.5x higher style-matching
accuracy than zero-shot. Llama/Qwen/Mixtral families, academic essays,
TF-IDF character n-grams + transformer embeddings, unsupervised distance
distributions.

**How it differs from us:**
- **Register:** academic essays — a conventionalized register with low
  within-genre variance; our target is literary fiction where the
  authorial signature is the object of interest.
- **Criterion:** "style match" = agreement under their own verifier's
  empirical distance threshold — a *binary same/different call*, not
  placement inside a target author's own variation distribution. Their
  verifier answers "more like A than like not-A"; our criterion is "as
  close to A as A is to herself."
- **Condition:** the 99.9% figure is for *text completion* — the model
  continues the author's own text, inheriting topic, register, and
  lexical context. This is the easiest possible conditioning and closest
  to our few-shot exemplar condition (C3/P4), which we have not yet run —
  flag this as the one cell where their result pressures ours.
- **Their own caveat does our work:** matched outputs remain separable by
  perplexity (15.2 vs human 29.5); they explicitly conclude "stylistic
  fidelity and statistical detectability are separable."

**What we must say:** cite as the clearest demonstration that *the
measurement frame determines the verdict*: under verifier-agreement the
imitation "succeeds," under a residual statistical signature it fails.
Our W/B percentile frame adjudicates this by putting both on one
calibrated scale. Also: their text-completion result obligates us to run
the exemplar-laden condition (P4/C3) before claiming generality of
"never enters."

### 1.3 Wang et al. 2025 — "Catch Me If You Can? Not Yet" (Findings of EMNLP 2025; arXiv:2509.14543)

**Their claim (mixed, mostly failure):** across 400+ everyday authors and
six frontier models, in-context imitation largely fails (zero-shot
accuracy <7%) but works "reasonably well" for structured formats (news,
email).

**How it differs from us:** everyday short texts, attribution/verification
ensemble criterion, everyday authors (the model has never seen their
text in training; our canonical literary targets are *maximally*
represented in pretraining — and still aren't entered). Their
domain-dependence (structured registers easier) supports our scoping:
literary voice is the hard end.

**What we must say:** convergent failure result; cite for the "even
famous-author advantage doesn't close the gap" argument: if models can't
enter the W region of authors whose complete works they have memorized,
data scarcity is not the binding constraint — the model-typical chassis is.

### 1.4 Persona/style-prompting effectiveness literature (2025-26)

Persona-prompting work (e.g., sociodemographic persona evaluation,
arXiv:2507.16076; psychological steering, arXiv:2510.04484; style
modulation heads, arXiv:2603.13249) reports that prompting *does* steer
measurable style properties, with prompting "consistently effective but
limited in intensity control." None of it measures entry into an
individual author's calibrated variation; effects are group-level or
trait-level.

**What we must say:** our R2 *agrees* that style prompting works
directionally (9/16 nearest-neighbor hits) — we are not claiming
prompting is inert. The contribution is showing where the effect
saturates: texture moves, the function-word chassis does not. This
positions us as reconciling, not contradicting, the persona literature.

---

## 2. The convergent class: imitation-fails / signature-persists results

These papers reach our direction by other roads; we must differentiate by
*measurement contribution*, since the headline ("LLMs don't fully
replicate individual style") is no longer novel by itself.

| Paper | Setting | Criterion | What we add beyond it |
|---|---|---|---|
| **Mikros 2025 (DSH)** — GPT-4o imitating Hemingway/Shelley, 45 texts of 1.4-2k words, MFW+LIWC+n-grams, Random Forest 84% | literary, closest topic neighbor | classifier accuracy + cluster visualization | calibrated W/B percentiles; 4 targets x 4+ models vs 1 model x 2 targets; 3.5k+ words; validated measurement space with pre-registered gates; the *approach* half (direction succeeds) which accuracy can't express |
| **Zeng & Nini 2026 (arXiv:2603.29454)** — GPT-4o impersonation vs forensic AV; impersonations easier to reject than genuine impostors | forensic short genres | likelihood-ratio AV decisions | literary long-form; distance scale (their "easier to reject than impostors" = our "AI beyond B median," independently replicated) |
| **Sawant 2026 (arXiv:2604.26460)** — personalization scores below the cross-author floor; human ceiling 0.756, floor 0.626, methods 0.484-0.508 | everyday personalization | calibrated verifier-score baselines | see §3 — nearest framing neighbor |
| **Alsadhan 2026 (DSH)** — Whitman/Wordsworth/Trump/Obama; GPT-4o/Gemini/Claude; 8 stylometric features detect mimicry | poetry/speeches | XGBoost/BERT detection | long-form fiction; placement not detection; per-author calibration |
| **O'Sullivan 2025 (HSSC)** — Burrows Delta (100 MFW) on 150-500-word stories; LLMs cluster tightly by model, humans heterogeneous | creative writing, closest method neighbor | Delta clustering/MDS visualization | quantified placement (percentiles, CIs) vs visualization; 10-20x longer texts; imitation condition; validation gates |
| **Reinhart et al. 2025 (PNAS)** — instruction-tuned models keep a noun-heavy dense style across registers, even when prompted to match | register adaptation | Biber-dimension contrasts | named-author identity space; their result is our R3 mechanism citation (chassis persists under style prompts) |
| **Bitton et al. 2025 (arXiv:2503.01659)** — model-family fingerprints persist under style prompts; 0.9988 precision | model attribution | classifier ensemble | inverse question; cite for R1/R4 framing |
| **Dentella et al. 2025 (arXiv:2508.16385)** — ChatGPT's grammatical backbone (tense/aspect/mood, noun preference) identifies it as non-human; limited cross-register variation | register stylometry | multidimensional analysis | function-word/MFW identity placement; their restricted-variation result prefigures our C5 |
| **Przystalski et al. 2026 (ESWA)** — stylometry separates human/LLM at 10 sentences, acc. up to .98 | detection, short text | tree classifiers | not detection; calibrated placement; literary register |

**Shared reconciliation line for the paper (§2/§7):** the field has
converged on "separable, homogeneous, signature-persists" via detector
and classifier evidence; what is missing — and what we supply — is *an
interpretable unit for how far*, anchored to the only natural yardstick:
how much the target author varies from herself.

---

## 3. Nearest-framing analysis: has anyone done within-author-variation calibration?

**Direct hit: none found.** Searches for within-author / intra-author
variation used as a *calibration distribution* for placing AI text (as
percentiles of W, with B as the far anchor) returned no prior instance in
2024-2026 literature, nor in classical stylometry applied to LLMs.

**Near-misses, in decreasing proximity:**

1. **Sawant 2026 (arXiv:2604.26460)** — the only other work that builds
   *calibrated baselines* (human ceiling = same-author agreement,
   cross-author floor) and interprets LLM output placement against them.
   Differences that preserve our claim: (a) the scale is a verifier
   score, not a distance distribution — no percentiles, no bootstrap CIs
   on W/B, no per-author regions; (b) everyday personalization, 50
   anonymous authors, not literary fiction or named-target imitation;
   (c) no length dimension (our 3k-word claim floor and E6 length curve
   have no analogue); (d) preprint, single-author, April 2026 — cite it
   generously and precisely. **This is the paper a reviewer will wave at
   us; pre-empt by name.**
2. **Zeng & Nini 2026** — likelihood-ratio AV implicitly compares
   same-author vs different-author score distributions (the forensic
   W/B analogue), but reports binary verification outcomes, not
   placement percentiles, and never frames "how far inside/outside."
3. **O'Sullivan 2025** — uses aggregate human diversity as the comparison
   point under Delta but explicitly does *not* calibrate within-author
   variation (no per-author W; humans are crowdworkers with one text
   each, so W is undefined in his design).
4. **Forensic validation literature** (Ishihara et al. 2024, already in
   catalog) — likelihood-ratio calibration culture is where our framing
   intellectually lives; cite to show the frame is imported from forensic
   text comparison and applied to a new question, not invented ex nihilo.

---

## 4. Honest novelty assessment

**No longer novel (do not claim):**
- "LLM text is stylometrically distinguishable from human text" — settled
  many times over (O'Sullivan, Przystalski, Bitton, Dentella, Reinhart).
- "LLMs cannot fully replicate a named author's style" — Mikros 2025 and
  Alsadhan 2026 both publish this conclusion for literary figures with
  multi-feature stylometry; Wang 2025 and Zeng & Nini 2026 for everyday
  authors. The *qualitative finding* is established.
- "LLM output is homogeneous / low-variance" — O'Sullivan, Dentella,
  Bitton; our C5 must be framed as quantification (a model's own W
  distribution on the same scale as human W), not discovery.
- Calibrated-baseline evaluation of style personalization *in general* —
  Sawant 2026 got there first in the personalization setting.

**Still novel after the sweep (claim, with the stated scope):**
1. **The unit of claim:** percentile-of-within-author-variation placement
   of AI text under Delta, with bootstrap CIs and pre-registered
   validation gates (E1-E3, E6) on a purpose-built literary shelf. Nobody
   reports "beyond W-p98" or "0/N inside W-p90" style numbers.
2. **Approach-without-entering as a two-part finding:** direction
   succeeds (nearest-neighbor hits) while region entry fails (0/N).
   Classifier-framing papers structurally cannot express this; it is our
   most distinctive empirical shape and reconciles the persona-prompting
   "it works" literature with the imitation "it fails" literature.
3. **Long-form literary setting:** every contrast paper operates at
   150-2,000 words; our 3,500-word samples with a 3,000-word claim floor
   and an explicit length-sensitivity curve (E6, C4) are unoccupied
   territory.
4. **The R3 mechanism analysis** (which interpretable dimensions move
   under style prompting vs the immobile MFW chassis) — Reinhart shows
   chassis-persistence for registers; nobody has the per-dimension
   movement decomposition for named-author imitation.
5. **The translation bound (R5)** — no analogue found anywhere in the
   sweep; "translation preserves more authorial signal than style
   prompting achieves" appears to be an unclaimed one-liner.

**Genuine scoop risk:**
- **Sawant 2026 (arXiv:2604.26460)** is the only near-scoop of the
  *framing* (claim C-C): calibrated human-ceiling/cross-author-floor
  evaluation showing personalization falls below the floor. It does not
  touch claims C-A or C-B (no literary fiction, no long form, no named
  authors, no distance percentiles). Mitigation: cite it as convergent
  framing in a different setting; sharpen our contribution statement to
  "percentile placement in a *distance-calibrated author space*" rather
  than "calibrated evaluation" generically. Risk level: moderate for
  framing-priority, nil for the empirical claims.
- **Mikros 2025 (DSH)** is the near-scoop of the *topic* (literary
  imitation, stylometric verdict). It is a 1-model/2-author classifier
  study; risk to our claims is nil, but failure to cite it prominently
  would be a desk-reject-grade omission at DSH/CHR venues.
- No paper found doing within-author percentile placement of long-form
  AI fiction. The window is open but visibly closing: four of the
  closest papers are dated 2026.

**Action items fed back into the outline:**
- P4 (few-shot exemplar condition) is now *blocking* for the generality
  of C-B, because Jemama & Kumar's 99.9% text-completion result will be
  the reviewer's first objection.
- §2 must engage Jones 2022 with the E6 length argument explicitly.
- Cite Sawant 2026 and Ishihara 2024 wherever the calibration frame is
  introduced; claim the *distance-percentile* frame, not calibration per se.
- Add Reinhart 2025 (PNAS) as the mechanism citation for R3 and
  Altakrori 2021 + Evert 2017 as the C1/feature-validity anchors.
