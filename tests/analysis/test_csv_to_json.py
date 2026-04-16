"""Tests for src/analysis/csv_to_json.py — convert_csv_to_json()."""

import json
import pytest
from pathlib import Path
from csv_to_json import convert_csv_to_json

EXPECTED_FIELDS = [
    "source", "period", "year_month", "mean_sentiment", "median_sentiment",
    "positive_pct", "neutral_pct", "negative_pct", "sentence_count", "sentiment_std",
]


class TestConvertCsvToJson:
    def test_output_is_valid_json(self, tmp_path, sample_monthly_sentiment_csv):
        out = tmp_path / "out.json"
        convert_csv_to_json(sample_monthly_sentiment_csv, out)
        content = out.read_text(encoding="utf-8")
        data = json.loads(content)  # raises if invalid
        assert isinstance(data, list)

    def test_row_count_matches(self, tmp_path, sample_monthly_sentiment_csv):
        out = tmp_path / "out.json"
        convert_csv_to_json(sample_monthly_sentiment_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 2  # fixture has 2 rows

    def test_all_fields_present(self, tmp_path, sample_monthly_sentiment_csv):
        out = tmp_path / "out.json"
        convert_csv_to_json(sample_monthly_sentiment_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        for entry in data:
            for field in EXPECTED_FIELDS:
                assert field in entry, f"Missing field: {field}"

    def test_numeric_types_correct(self, tmp_path, sample_monthly_sentiment_csv):
        out = tmp_path / "out.json"
        convert_csv_to_json(sample_monthly_sentiment_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        for entry in data:
            assert isinstance(entry["mean_sentiment"], float)
            assert isinstance(entry["sentence_count"], int)
            assert isinstance(entry["positive_pct"], float)
            assert isinstance(entry["sentiment_std"], float)

    def test_string_fields_correct(self, tmp_path, sample_monthly_sentiment_csv):
        out = tmp_path / "out.json"
        convert_csv_to_json(sample_monthly_sentiment_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        for entry in data:
            assert isinstance(entry["source"], str)
            assert isinstance(entry["period"], str)
            assert isinstance(entry["year_month"], str)

    def test_values_correct(self, tmp_path, sample_monthly_sentiment_csv):
        out = tmp_path / "out.json"
        convert_csv_to_json(sample_monthly_sentiment_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        first = data[0]
        assert first["source"] == "bbc_news_tv"
        assert first["year_month"] == "2020-03"
        assert first["mean_sentiment"] == pytest.approx(0.5)
        assert first["sentence_count"] == 10
