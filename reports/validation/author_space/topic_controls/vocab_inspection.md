# Wave-2 Top-300 MFW Vocabulary Inspection (C1, issue #95 P3)

- Artifact inspected: `data/artifacts/author_space_v1_wave2.json`
  (15 authors, 78 works, `distance_variant=mfw_delta`, N=300, `vocab_filter` absent = none)
- Reference list: `mnemosyne.core.author_space.STYLOMETRIC_FUNCTION_WORDS`
  (376 closed-class entries: determiners, pronouns, prepositions,
  conjunctions, auxiliaries/modals, closed-class adverbs/particles, plus the
  tokenizer-compatibility contraction families; see the docstring in
  `author_space.py` for the construction and citations)
- Machine-readable companion: `vocab_inspection.json`

## Headline

**140 of 300 vocabulary words (46.7%) are NOT closed-class function words.**
The unfiltered top-300 MFW vocabulary is roughly half open-class material —
mostly high-frequency lexical verbs and adjectives, but it includes plainly
content-bearing concrete nouns and even one proper name. The topic-confound
worry is therefore legitimate on its face and worth the function-words-only
control (`fwonly_comparison.md`).

## Classification of the 140 non-closed-class entries

| Bucket | n | Examples (vocab rank) |
|---|---|---|
| Proper names / titles | 2 | tengo (294), mr (186) |
| Person & kinship nouns | 9 | man (79), people (102), father (174), mother (200), children (295) |
| Body & voice nouns | 8 | eyes (130), face (139), hand (147), hair (245), voice (279) |
| Concrete place/object nouns | 17 | room (125), house (153), door (164), window (278), street (276), car (298), water (207) |
| Time/life nouns | 9 | time (61), day (122), night (148), year (299), moment (264) |
| Abstract/misc nouns | 12 | way (80), thing (149), mind (229), love (281), course (236) |
| High-frequency lexical verbs | 55 | said (28), know (69), looked (111), thought (121), went (114), asked (213) |
| Adjectives | 25 | little (86), old (96), white (169), black (209), dark (216), dead (288) |
| Numerals / interjections (borderline closed-class) | 3 | two (87), three (185), yes (193) |

Notes:

- `tengo` (rank 294) is a character name from Murakami's *1Q84* — direct
  proper-noun leakage of one shelf author's content into the measurement
  vocabulary. `mr` is a title token concentrated in dialogue-heavy and
  period-set works.
- `dont` (rank 293) IS counted as closed-class here: it is McCarthy's
  unapostrophized "don't", i.e. an auxiliary in author-specific spelling —
  itself a nice example of why a principled list beats a stop-word list.
- The lexical-verb bucket (55 words) is the biggest open-class block. Verbs
  like *said/looked/thought* are stylometrically classic and only weakly
  topical, but they are not closed-class and are removed by the filter.

## Top 20 most content-bearing entries (manual ranking)

| # | Word | Vocab rank | Why contenty |
|---|---|---|---|
| 1 | tengo | 294 | proper name (Murakami, *1Q84*) |
| 2 | mr | 186 | title; period/register marker |
| 3 | car | 298 | concrete object, setting-dependent |
| 4 | street | 276 | urban setting |
| 5 | window | 278 | concrete object |
| 6 | table | 248 | concrete object |
| 7 | bed | 262 | concrete object |
| 8 | floor | 292 | concrete object |
| 9 | door | 164 | concrete object |
| 10 | house | 153 | setting |
| 11 | room | 125 | setting |
| 12 | hair | 245 | body description |
| 13 | eyes | 130 | body description |
| 14 | face | 139 | body description |
| 15 | head | 134 | body description |
| 16 | hands | 205 | body description |
| 17 | body | 256 | body description |
| 18 | water | 207 | nature/setting |
| 19 | father | 174 | kinship, plot-dependent |
| 20 | mother | 200 | kinship, plot-dependent |

The full 140-word list with vocabulary ranks is in `vocab_inspection.json`
(`content_words_with_rank`).
