"""Tests for src/preprocessing/filter_relevant_loose.py — COVID_REGEX."""

import pytest
from filter_relevant_loose import COVID_REGEX


class TestCovidRegex:
    def test_direct_term_matches(self):
        assert COVID_REGEX.search("The covid situation is serious.") is not None

    def test_indirect_term_matches(self):
        # Loose filter requires only one term (direct or indirect)
        assert COVID_REGEX.search("The lockdown was difficult.") is not None

    def test_pandemic_matches(self):
        assert COVID_REGEX.search("The pandemic changed everything.") is not None

    def test_no_term_no_match(self):
        assert COVID_REGEX.search("The weather was sunny yesterday.") is None

    def test_case_insensitive(self):
        assert COVID_REGEX.search("COVID cases rose.") is not None
        assert COVID_REGEX.search("Coronavirus spread.") is not None

    def test_word_boundary(self):
        # "epicovid" should not match via word boundary
        assert COVID_REGEX.search("The epicovid study.") is None

    def test_vaccine_matches(self):
        assert COVID_REGEX.search("The vaccine rollout began.") is not None

    def test_nhs_matches(self):
        assert COVID_REGEX.search("The nhs was under pressure.") is not None


class TestLooseFilterFileOutput:
    def test_file_only_created_if_matches(self, tmp_path):
        """Output file should not be created if no sentences match."""
        input_file = tmp_path / "Jan 2020.txt"
        input_file.write_text("The weather was sunny.\nThe birds were singing.\n")
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output_file = output_dir / "Jan 2020.txt"

        sentences = input_file.read_text(encoding="utf-8").splitlines()
        relevant = [s.strip() for s in sentences if COVID_REGEX.search(s)]

        if relevant:
            output_file.write_text("\n".join(relevant) + "\n", encoding="utf-8")

        assert not output_file.exists()

    def test_file_created_with_matches(self, tmp_path):
        """Output file should contain only matching sentences."""
        input_file = tmp_path / "Jan 2020.txt"
        input_file.write_text(
            "The weather was sunny.\nThe covid cases rose sharply.\nBirds sang.\n"
        )
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        output_file = output_dir / "Jan 2020.txt"

        sentences = input_file.read_text(encoding="utf-8").splitlines()
        relevant = [s.strip() for s in sentences if COVID_REGEX.search(s)]

        if relevant:
            output_file.write_text("\n".join(relevant) + "\n", encoding="utf-8")

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "covid cases rose sharply" in content
        assert "weather" not in content
        assert "Birds" not in content
