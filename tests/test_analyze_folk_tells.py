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


class TestPaperConfigurationCertification:
    """An artifact's name is a claim; content and shape are the certification.

    Before the cross-family review of 2026-08-07 (finding F2), a file
    renamed to the paper's artifact name was stamped
    is_paper_configuration = true on that basis alone. These pin that the
    artifact's sha256 and the run's structural facts decide it, and that a
    mismatch stops the run instead of labelling the output as the paper's.
    """

    def test_matching_structure_certifies(self):
        ft.assert_paper_configuration("author_space_v1_wave2.json", [
            ("shelf works", ft.PAPER_HUMAN_WORKS, ft.PAPER_HUMAN_WORKS),
            ("shelf authors", ft.PAPER_HUMAN_AUTHORS, ft.PAPER_HUMAN_AUTHORS),
        ])

    def test_wrong_shelf_size_hard_fails(self):
        with pytest.raises(SystemExit) as excinfo:
            ft.assert_paper_configuration("author_space_v1_wave2.json", [
                ("shelf works", 35, ft.PAPER_HUMAN_WORKS),
                ("shelf authors", 9, ft.PAPER_HUMAN_AUTHORS),
            ])
        message = str(excinfo.value)
        assert "THE RUN DOES NOT" in message
        # The message must name what differed, on both sides.
        assert "shelf works: this run 35, paper run 78" in message
        assert "shelf authors: this run 9, paper run 15" in message

    def test_changed_run_parameter_hard_fails(self):
        with pytest.raises(SystemExit) as excinfo:
            ft.assert_paper_configuration("author_space_v1_wave2.json", [
                ("--seed", 1234, ft.PAPER_SEED),
            ])
        assert "--seed: this run 1234" in str(excinfo.value)

    def test_wrong_content_hash_hard_fails(self):
        with pytest.raises(SystemExit) as excinfo:
            ft.assert_paper_configuration("author_space_v1_wave2.json", [
                ("artifact sha256", "0" * 64, ft.PAPER_ARTIFACT_SHA256),
            ])
        assert "artifact sha256" in str(excinfo.value)

    def test_local_hash_helper_matches_the_canonical_one(self):
        """The local _sha256_of_file mirrors author_manifold's; pin that."""
        from author_manifold.author_space import sha256_of_file
        path = REPO_ROOT / "data/artifacts" / ft.PAPER_ARTIFACT
        assert ft._sha256_of_file(path) == sha256_of_file(path)

    def test_pinned_hash_is_the_hash_the_release_already_declares(self):
        """Provenance: the sidecar's declaration, the constant, the bytes."""
        import json
        sidecar = json.loads(
            (REPO_ROOT / "data/artifacts/lm_envelopes_wave2_3000w.json")
            .read_text(encoding="utf-8"))
        assert sidecar["meta"]["source_artifact"].endswith(ft.PAPER_ARTIFACT)
        assert (sidecar["meta"]["source_artifact_sha256"]
                == ft.PAPER_ARTIFACT_SHA256)
        assert ft._sha256_of_file(
            REPO_ROOT / "data/artifacts" / ft.PAPER_ARTIFACT
        ) == ft.PAPER_ARTIFACT_SHA256

    @pytest.mark.integration
    def test_mutated_artifact_is_refused_before_any_text_is_read(
            self, tmp_path):
        """Right shelf, one MFW centroid changed: only content identity sees it.

        Also pins that the refusal happens before load_human_works, which
        would otherwise fail on the rights-encumbered texts instead.
        """
        import json
        import subprocess
        artifact = json.loads(
            (REPO_ROOT / "data/artifacts" / ft.PAPER_ARTIFACT)
            .read_text(encoding="utf-8"))
        slug = sorted(artifact["authors"])[0]
        artifact["authors"][slug]["mfw_centroid"][0] += 0.01
        impostor = tmp_path / ft.PAPER_ARTIFACT
        impostor.write_text(json.dumps(artifact), encoding="utf-8")

        out_dir = tmp_path / "out"
        proc = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools/analyze_folk_tells.py"),
             "--space-artifact", str(impostor), "--output-dir", str(out_dir)],
            capture_output=True, text=True)
        output = proc.stdout + proc.stderr
        assert proc.returncode != 0, output
        assert "THE RUN DOES NOT" in output
        assert "artifact sha256" in output
        assert not out_dir.exists() or not list(out_dir.iterdir())

    def test_pinned_expectations_match_the_committed_evidence(self):
        """The constants are transcribed from the recorded run; check that."""
        import json
        meta = json.loads(
            (REPO_ROOT / "reports/validation/author_space/results2"
             / "folk_tells.json").read_text(encoding="utf-8"))["meta"]
        assert meta["n_human_works"] == ft.PAPER_HUMAN_WORKS
        assert meta["n_human_authors"] == ft.PAPER_HUMAN_AUTHORS
        assert meta["n_human_windows"] == ft.PAPER_HUMAN_WINDOWS
        assert meta["n_ai_samples"] == ft.PAPER_AI_SAMPLES
        assert meta["n_ai_models"] == ft.PAPER_AI_MODELS
        assert meta["window_words"] == ft.PAPER_WINDOW_WORDS
        assert meta["max_windows_per_work"] == ft.PAPER_MAX_WINDOWS_PER_WORK
        assert meta["seed"] == ft.PAPER_SEED
        assert meta["n_bootstrap"] == ft.PAPER_N_BOOTSTRAP
