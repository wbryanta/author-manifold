"""Unit tests for the folk-tell counters and stats in analyze_folk_tells.py.

The counters are conservative regex/heuristics; these tests pin their
behavior on constructed snippets (true positives counted, documented
exclusions not counted) and the AUC/threshold machinery on known values.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "tools"))

import analyze_folk_tells as ft  # noqa: E402


def count(tell_id, text):
    counters = {tid: fn for tid, _, fn in ft.TELLS}
    return counters[tell_id](text)


class TestCounters:
    def test_em_dash_counts_both_forms(self):
        assert count("em_dash", "a — b and c -- d") == 2

    def test_em_dash_ignores_triple_hyphen_rule(self):
        # standalone -- only; --- (markdown rule) is not two em dashes
        assert count("em_dash", "a --- b") == 0

    def test_not_x_but_y(self):
        assert count("not_x_but_y", "It was not anger, but grief.") == 1
        assert count("not_x_but_y", "It's not the fall, it's the landing.") == 1
        # 'not only ... but also' (classical rhetoric) excluded
        assert count("not_x_but_y", "not only smart, but also kind") == 0
        # cross-sentence 'not ... but' not counted
        assert count("not_x_but_y", "He did not go. But she did.") == 0

    def test_tricolon_serial_triad(self):
        assert count("tricolon", "cold, dark, and wet") == 1
        assert count("tricolon", "the night, the road, and rain") == 1
        # two items only — not a triad
        assert count("tricolon", "cold and wet") == 0
        # conservative: 3-word items are documented as missed
        assert count("tricolon",
                     "the cold dark night, the long wet road, and rain") == 0

    def test_exclamation(self):
        assert count("exclamation", "No! Stop! Please.") == 2

    def test_lets_opener_sentence_initial_only(self):
        assert count("lets_opener", "Let's begin. Then we stop.") == 1
        assert count("lets_opener", "He said. Let's go now.") == 1
        # mid-sentence "let's" is not an opener
        assert count("lets_opener", "then let's go") == 0

    def test_superlative(self):
        assert count("superlative", "the greatest, the most beautiful") == 2
        assert count("superlative", "the best and the worst") == 2
        # blocklisted -est words
        assert count("superlative", "an honest harvest in the forest") == 0
        # bare 'most + noun' not counted (own tell territory)
        assert count("superlative", "most people think") == 0

    def test_delve_leverage_lemmas(self):
        assert count("delve_leverage", "We delved in, leveraging it.") == 2
        assert count("delve_leverage", "the lever moved") == 0

    def test_corporate_jargon(self):
        assert count("corporate_jargon",
                     "a scalable, holistic paradigm for stakeholders") == 4
        assert count("corporate_jargon", "she walked to the store") == 0

    def test_hedges_exclude_bare_modals(self):
        assert count("hedges", "Perhaps it was, arguably, enough.") == 2
        assert count("hedges", "He may go. She might stay.") == 0

    def test_staging_adverbs(self):
        assert count("staging_adverbs", "quietly devastating, softly lit") == 2

    def test_container_words_framing_only(self):
        assert count("container_words", "a space for grief") == 1
        assert count("container_words", "an opportunity to grow") == 1
        # literal space not counted
        assert count("container_words", "the space between the houses") == 0

    def test_unnamed_consensus(self):
        assert count("unnamed_consensus",
                     "Most people agree; studies show it.") == 2


class TestStats:
    def test_auc_perfect_separation(self):
        assert ft.mann_whitney_auc(np.array([3.0, 4.0]), np.array([1.0, 2.0])) == 1.0

    def test_auc_chance_on_identical(self):
        assert ft.mann_whitney_auc(np.array([1.0, 2.0]),
                                   np.array([1.0, 2.0])) == pytest.approx(0.5)

    def test_auc_inverted(self):
        assert ft.mann_whitney_auc(np.array([1.0, 2.0]), np.array([3.0, 4.0])) == 0.0

    def test_tell_stats_degenerate_when_ai_median_zero(self):
        rng = np.random.default_rng(0)
        ai = np.array([0.0] * 6 + [1.0] * 4)
        human = np.abs(rng.normal(1, 0.5, 40))
        s = ft.tell_stats("t", ai, ["m"] * 10, human, ["a"] * 40, rng, 50)
        assert s["witch_hunt"]["degenerate_threshold"] is True
        assert s["witch_hunt"]["most_flagged_authors"] == []

    def test_tell_stats_not_degenerate_for_signed_scores(self):
        rng = np.random.default_rng(0)
        ai = rng.normal(-1, 1, 50)       # negative median, signed values
        human = rng.normal(0, 1, 50)
        s = ft.tell_stats("z", ai, ["m"] * 50, human, ["a"] * 50, rng, 50)
        assert s["witch_hunt"]["degenerate_threshold"] is False

    def test_rates_per_1000_words(self):
        text = "a — b " * 10  # 10 em dashes, 30 words
        rates = ft.rates_for(text, 30)
        assert rates["em_dash"] == pytest.approx(10 * 1000 / 30)


class TestWindowing:
    def test_iter_windows_deterministic_and_word_exact(self):
        text = " ".join(f"w{i}" for i in range(40))
        rng1 = np.random.default_rng(7)
        rng2 = np.random.default_rng(7)
        w1 = list(ft.iter_windows(text, rng1, window_words=10, max_windows=3))
        w2 = list(ft.iter_windows(text, rng2, window_words=10, max_windows=3))
        assert w1 == w2
        assert len(w1) == 3
        for _, chunk in w1:
            assert len(chunk.split()) == 10

    def test_iter_windows_short_text_yields_nothing(self):
        assert list(ft.iter_windows("too short",
                                    np.random.default_rng(0),
                                    window_words=10)) == []
