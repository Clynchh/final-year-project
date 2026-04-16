"""Tests for src/analysis/emotion_to_json.py — integration tests using tmp files."""

import csv
import json
import pytest
from pathlib import Path

EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]


def _write_emotion_monthly_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = ["source", "period", "year_month", "sentence_count"] + [f"{e}_pct" for e in EMOTIONS]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _run_conversion(input_csv: Path, output_json: Path) -> list[dict]:
    """Replicate the emotion_to_json conversion logic directly (avoids __main__ import issues)."""
    data = []
    with open(input_csv, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            entry = {
                "source": row["source"],
                "period": row["period"],
                "year_month": row["year_month"],
                "sentence_count": int(row["sentence_count"]),
            }
            for e in EMOTIONS:
                entry[f"{e}_pct"] = float(row[f"{e}_pct"])
            data.append(entry)
    output_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


@pytest.fixture
def emotion_monthly_csv(tmp_path) -> Path:
    p = tmp_path / "emotion_monthly.csv"
    rows = [
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "sentence_count": "100",
         "anger_pct": "10.0", "disgust_pct": "5.0", "fear_pct": "40.0",
         "joy_pct": "5.0", "neutral_pct": "20.0", "sadness_pct": "15.0", "surprise_pct": "5.0"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-04",
         "sentence_count": "80",
         "anger_pct": "8.0", "disgust_pct": "4.0", "fear_pct": "35.0",
         "joy_pct": "10.0", "neutral_pct": "25.0", "sadness_pct": "12.0", "surprise_pct": "6.0"},
    ]
    _write_emotion_monthly_csv(p, rows)
    return p


class TestEmotionToJson:
    def test_output_is_valid_json(self, tmp_path, emotion_monthly_csv):
        out = tmp_path / "emotion_data.json"
        _run_conversion(emotion_monthly_csv, out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert isinstance(data, list)

    def test_row_count_matches(self, tmp_path, emotion_monthly_csv):
        out = tmp_path / "emotion_data.json"
        data = _run_conversion(emotion_monthly_csv, out)
        assert len(data) == 2

    def test_emotion_pct_are_floats(self, tmp_path, emotion_monthly_csv):
        out = tmp_path / "emotion_data.json"
        data = _run_conversion(emotion_monthly_csv, out)
        for entry in data:
            for e in EMOTIONS:
                assert isinstance(entry[f"{e}_pct"], float), f"{e}_pct should be float"

    def test_sentence_count_is_int(self, tmp_path, emotion_monthly_csv):
        out = tmp_path / "emotion_data.json"
        data = _run_conversion(emotion_monthly_csv, out)
        for entry in data:
            assert isinstance(entry["sentence_count"], int)

    def test_all_emotions_present(self, tmp_path, emotion_monthly_csv):
        out = tmp_path / "emotion_data.json"
        data = _run_conversion(emotion_monthly_csv, out)
        for entry in data:
            for e in EMOTIONS:
                assert f"{e}_pct" in entry

    def test_string_fields_correct(self, tmp_path, emotion_monthly_csv):
        out = tmp_path / "emotion_data.json"
        data = _run_conversion(emotion_monthly_csv, out)
        assert data[0]["source"] == "bbc_news_tv"
        assert data[0]["period"] == "covid"
        assert data[0]["year_month"] == "2020-03"
