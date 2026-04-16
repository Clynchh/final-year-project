"""Tests for src/analysis/sentence_count_to_json.py — convert_csv_to_json()."""

import json
import pytest
from pathlib import Path
from sentence_count_to_json import convert_csv_to_json


class TestSentenceCountToJson:
    def test_output_is_valid_json(self, tmp_path, sample_sentence_count_csv):
        out = tmp_path / "sentence_count.json"
        convert_csv_to_json(sample_sentence_count_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)

    def test_row_count_matches(self, tmp_path, sample_sentence_count_csv):
        out = tmp_path / "sentence_count.json"
        convert_csv_to_json(sample_sentence_count_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert len(data) == 3  # fixture has 3 rows

    def test_year_is_int(self, tmp_path, sample_sentence_count_csv):
        out = tmp_path / "sentence_count.json"
        convert_csv_to_json(sample_sentence_count_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        for entry in data:
            assert isinstance(entry["year"], int), "year should be int"

    def test_count_is_int(self, tmp_path, sample_sentence_count_csv):
        out = tmp_path / "sentence_count.json"
        convert_csv_to_json(sample_sentence_count_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        for entry in data:
            assert isinstance(entry["count"], int), "count should be int"

    def test_month_is_string(self, tmp_path, sample_sentence_count_csv):
        out = tmp_path / "sentence_count.json"
        convert_csv_to_json(sample_sentence_count_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        for entry in data:
            assert isinstance(entry["month"], str)

    def test_values_correct(self, tmp_path, sample_sentence_count_csv):
        out = tmp_path / "sentence_count.json"
        convert_csv_to_json(sample_sentence_count_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        first = data[0]
        assert first["month"] == "Jan"
        assert first["year"] == 2020
        assert first["count"] == 150
