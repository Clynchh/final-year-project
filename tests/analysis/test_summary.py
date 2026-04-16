"""Tests for src/analysis/summary.py — summarise_sentiment() and summarise_emotions()."""

import csv
import pytest
from pathlib import Path
from summary import summarise_sentiment, summarise_emotions, EMOTIONS


def read_csv(path: Path) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class TestSummariseSentiment:
    def test_mean_correct(self, tmp_path, sample_sentiment_csv):
        out = tmp_path / "monthly.csv"
        summarise_sentiment(sample_sentiment_csv, out)
        rows = read_csv(out)
        # bbc_news_tv covid 2020-03 has scores [1, -1] → mean = 0.0
        row = next(r for r in rows if r["year_month"] == "2020-03" and r["source"] == "bbc_news_tv")
        assert float(row["mean_sentiment"]) == pytest.approx(0.0)

    def test_positive_negative_percentages(self, tmp_path, sample_sentiment_csv):
        out = tmp_path / "monthly.csv"
        summarise_sentiment(sample_sentiment_csv, out)
        rows = read_csv(out)
        row = next(r for r in rows if r["year_month"] == "2020-03" and r["source"] == "bbc_news_tv")
        pos = float(row["positive_pct"])
        neg = float(row["negative_pct"])
        neu = float(row["neutral_pct"])
        assert pos + neg + neu == pytest.approx(100.0, abs=0.01)

    def test_groups_by_source_period_month(self, tmp_path, sample_sentiment_csv):
        out = tmp_path / "monthly.csv"
        summarise_sentiment(sample_sentiment_csv, out)
        rows = read_csv(out)
        # Should have separate rows for bbc_news_tv and bbc_radio4
        sources = {r["source"] for r in rows}
        assert "bbc_news_tv" in sources
        assert "bbc_radio4" in sources

    def test_sentence_count_correct(self, tmp_path, sample_sentiment_csv):
        out = tmp_path / "monthly.csv"
        summarise_sentiment(sample_sentiment_csv, out)
        rows = read_csv(out)
        row = next(r for r in rows if r["year_month"] == "2020-03" and r["source"] == "bbc_news_tv")
        assert int(row["sentence_count"]) == 2

    def test_std_single_value(self, tmp_path, tmp_path_factory):
        # Single-score group → std should be 0.0 (not raise an exception)
        p = tmp_path / "single.csv"
        fieldnames = ["source", "period", "year_month", "sentiment_label", "sentiment_score", "confidence"]
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
                             "sentiment_label": "positive", "sentiment_score": "1", "confidence": "0.9"})
        out = tmp_path / "monthly_single.csv"
        summarise_sentiment(p, out)
        rows = read_csv(out)
        assert float(rows[0]["sentiment_std"]) == 0.0

    def test_median_correct(self, tmp_path):
        # Three scores: [-1, 1, 1] → median = 1
        p = tmp_path / "three.csv"
        fieldnames = ["source", "period", "year_month", "sentiment_label", "sentiment_score", "confidence"]
        rows_in = [
            {"source": "s", "period": "covid", "year_month": "2020-01",
             "sentiment_label": "negative", "sentiment_score": "-1", "confidence": "0.8"},
            {"source": "s", "period": "covid", "year_month": "2020-01",
             "sentiment_label": "positive", "sentiment_score": "1", "confidence": "0.9"},
            {"source": "s", "period": "covid", "year_month": "2020-01",
             "sentiment_label": "positive", "sentiment_score": "1", "confidence": "0.85"},
        ]
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_in)
        out = tmp_path / "monthly_three.csv"
        summarise_sentiment(p, out)
        result = read_csv(out)
        assert float(result[0]["median_sentiment"]) == 1.0


class TestSummariseEmotions:
    def test_emotion_percentages_sum_to_100(self, tmp_path, sample_emotion_csv):
        out = tmp_path / "emotion_monthly.csv"
        summarise_emotions(sample_emotion_csv, out)
        rows = read_csv(out)
        for row in rows:
            total_pct = sum(float(row[f"{e}_pct"]) for e in EMOTIONS)
            assert total_pct == pytest.approx(100.0, abs=0.1)

    def test_emotion_groups_correctly(self, tmp_path, sample_emotion_csv):
        out = tmp_path / "emotion_monthly.csv"
        summarise_emotions(sample_emotion_csv, out)
        rows = read_csv(out)
        year_months = {r["year_month"] for r in rows}
        assert "2020-03" in year_months
        assert "2020-04" in year_months

    def test_emotion_zero_count_handled(self, tmp_path):
        # Empty input should not raise division by zero
        p = tmp_path / "empty_emotion.csv"
        fieldnames = ["source", "period", "year_month", "emotion", "confidence"]
        with open(p, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
        out = tmp_path / "empty_emotion_monthly.csv"
        summarise_emotions(p, out)  # should not raise
        rows = read_csv(out)
        assert rows == []

    def test_all_emotion_fields_present(self, tmp_path, sample_emotion_csv):
        out = tmp_path / "emotion_monthly.csv"
        summarise_emotions(sample_emotion_csv, out)
        rows = read_csv(out)
        for row in rows:
            for e in EMOTIONS:
                assert f"{e}_pct" in row

    def test_fear_dominant_in_march(self, tmp_path, sample_emotion_csv):
        out = tmp_path / "emotion_monthly.csv"
        summarise_emotions(sample_emotion_csv, out)
        rows = read_csv(out)
        march = next(r for r in rows if r["year_month"] == "2020-03")
        # 2 fear out of 3 sentences → ~66.67%
        assert float(march["fear_pct"]) == pytest.approx(66.67, abs=0.1)
