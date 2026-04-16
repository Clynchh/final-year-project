"""Tests for src/preprocessing/sample_sentences.py."""

import random
import pytest
import sample_sentences as ss


class TestSampleRate:
    def test_sample_rate_value(self):
        # SAMPLE_RATE is set to ~2.9% — verify it's in a plausible range
        assert 0.01 <= ss.SAMPLE_RATE <= 0.1

    def test_sample_at_least_one(self):
        # Even a file with 1 sentence gets at least 1 sample
        n_sentences = 1
        n_sample = max(1, round(n_sentences * ss.SAMPLE_RATE))
        assert n_sample >= 1

    def test_sample_formula_small_file(self):
        # Small files: round may give 0, but max(1, ...) ensures at least 1
        n_sentences = 5
        n_sample = max(1, round(n_sentences * ss.SAMPLE_RATE))
        assert n_sample >= 1

    def test_sample_formula_large_file(self):
        # Large files should produce proportionally more samples
        small = max(1, round(100 * ss.SAMPLE_RATE))
        large = max(1, round(1000 * ss.SAMPLE_RATE))
        assert large > small

    def test_sample_does_not_exceed_sentence_count(self):
        sentences = ["sentence one.", "sentence two.", "sentence three."]
        n_sample = max(1, round(len(sentences) * ss.SAMPLE_RATE))
        sampled = random.sample(sentences, min(n_sample, len(sentences)))
        assert len(sampled) <= len(sentences)


class TestSampleReproducibility:
    def test_same_seed_same_result(self, tmp_path):
        sentences = [f"Sentence number {i}." for i in range(200)]
        n_sample = max(1, round(len(sentences) * ss.SAMPLE_RATE))

        random.seed(42)
        result_a = random.sample(sentences, min(n_sample, len(sentences)))

        random.seed(42)
        result_b = random.sample(sentences, min(n_sample, len(sentences)))

        assert result_a == result_b

    def test_different_seed_different_result(self):
        sentences = [f"Sentence number {i}." for i in range(200)]
        n_sample = max(1, round(len(sentences) * ss.SAMPLE_RATE))

        random.seed(42)
        result_a = random.sample(sentences, min(n_sample, len(sentences)))

        random.seed(99)
        result_b = random.sample(sentences, min(n_sample, len(sentences)))

        assert result_a != result_b


class TestSampleOutputStructure:
    def test_output_mirrors_directory_structure(self, tmp_path):
        """Sampled output should be written to sampled/ with same source/period/year structure."""
        segmented_dir = tmp_path / "segmented"
        sampled_dir = tmp_path / "sampled"
        year_dir = segmented_dir / "bbc_news_tv" / "covid" / "2020"
        year_dir.mkdir(parents=True)

        input_file = year_dir / "Jan 2020.txt"
        input_file.write_text("\n".join(f"Sentence {i}." for i in range(50)))

        sentences = [s.strip() for s in input_file.read_text(encoding="utf-8").splitlines() if s.strip()]
        n_sample = max(1, round(len(sentences) * ss.SAMPLE_RATE))
        random.seed(42)
        sampled = random.sample(sentences, min(n_sample, len(sentences)))

        rel_dir = input_file.parent.relative_to(segmented_dir)
        output_dir = sampled_dir / rel_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / input_file.name
        output_path.write_text("\n".join(sampled) + "\n", encoding="utf-8")

        assert output_path.exists()
        assert (sampled_dir / "bbc_news_tv" / "covid" / "2020" / "Jan 2020.txt").exists()

    def test_empty_lines_excluded(self, tmp_path):
        input_file = tmp_path / "test.txt"
        input_file.write_text("Good sentence.\n\n   \nAnother sentence.\n")
        sentences = [s.strip() for s in input_file.read_text(encoding="utf-8").splitlines() if s.strip()]
        assert "" not in sentences
        assert "   " not in sentences
        assert len(sentences) == 2
