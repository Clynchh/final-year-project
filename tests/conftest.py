"""Shared fixtures and sys.path setup for the test suite."""

import csv
import sys
from pathlib import Path

# Make src/preprocessing and src/analysis importable without package prefix,
# matching how the scripts import from each other (e.g. "from constants import ...").
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src" / "preprocessing"))
sys.path.insert(0, str(PROJECT_ROOT / "src" / "analysis"))

import pytest


@pytest.fixture
def sample_sentiment_csv(tmp_path) -> Path:
    """Write a small sentiment details CSV and return its path."""
    p = tmp_path / "sentiment_details.csv"
    rows = [
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "sentiment_label": "positive", "sentiment_score": "1", "confidence": "0.9"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "sentiment_label": "negative", "sentiment_score": "-1", "confidence": "0.8"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-04",
         "sentiment_label": "positive", "sentiment_score": "1", "confidence": "0.85"},
        {"source": "bbc_radio4", "period": "covid", "year_month": "2020-03",
         "sentiment_label": "negative", "sentiment_score": "-1", "confidence": "0.7"},
    ]
    fieldnames = ["source", "period", "year_month", "sentiment_label", "sentiment_score", "confidence"]
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return p


@pytest.fixture
def sample_monthly_sentiment_csv(tmp_path) -> Path:
    """Write a small monthly sentiment summary CSV and return its path."""
    p = tmp_path / "sentiment_monthly.csv"
    rows = [
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "mean_sentiment": "0.5", "median_sentiment": "0.5",
         "positive_pct": "60.0", "neutral_pct": "10.0", "negative_pct": "30.0",
         "sentence_count": "10", "sentiment_std": "0.5"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-04",
         "mean_sentiment": "-0.2", "median_sentiment": "0.0",
         "positive_pct": "40.0", "neutral_pct": "20.0", "negative_pct": "40.0",
         "sentence_count": "5", "sentiment_std": "0.8"},
    ]
    fieldnames = [
        "source", "period", "year_month", "mean_sentiment", "median_sentiment",
        "positive_pct", "neutral_pct", "negative_pct", "sentence_count", "sentiment_std",
    ]
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return p


@pytest.fixture
def sample_emotion_csv(tmp_path) -> Path:
    """Write a small emotion details CSV and return its path."""
    p = tmp_path / "emotion_details.csv"
    rows = [
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "emotion": "fear", "confidence": "0.9"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "emotion": "neutral", "confidence": "0.7"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-03",
         "emotion": "fear", "confidence": "0.8"},
        {"source": "bbc_news_tv", "period": "covid", "year_month": "2020-04",
         "emotion": "joy", "confidence": "0.6"},
    ]
    fieldnames = ["source", "period", "year_month", "emotion", "confidence"]
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return p


@pytest.fixture
def sample_sentence_count_csv(tmp_path) -> Path:
    """Write a small sentence count CSV and return its path."""
    p = tmp_path / "sentence_count.csv"
    rows = [
        {"month": "Jan", "year": "2020", "count": "150"},
        {"month": "Feb", "year": "2020", "count": "200"},
        {"month": "Mar", "year": "2020", "count": "175"},
    ]
    with open(p, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["month", "year", "count"])
        writer.writeheader()
        writer.writerows(rows)
    return p
