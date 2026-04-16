# Aggregates per-sentence sentiment and emotion CSVs into monthly summary CSVs.

import csv
import re
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

_CURRENT = Path(__file__).resolve()
RESULTS = _CURRENT.parent.parent / "results"
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

_MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}
_MONTH_RE = re.compile(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{4})", re.IGNORECASE)


def _count_covid_sentences(covid_dir: Path) -> dict:
    """Count sentences per (source, period, year_month) in the filtered sample dir."""
    counts: dict = defaultdict(int)
    for txt_file in sorted(covid_dir.rglob("*.txt")):
        parts = txt_file.relative_to(covid_dir).parts
        source = parts[0] if len(parts) > 1 else "unknown"
        period = parts[1] if len(parts) > 2 else "unknown"
        month_match = _MONTH_RE.search(txt_file.name)
        if not month_match:
            continue
        month = _MONTH_MAP[month_match.group(1).lower()]
        year = month_match.group(2)
        sentences = [line for line in txt_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        counts[(source, period, f"{year}-{month}")] += len(sentences)
    return counts

EMOTIONS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]


def summarise_emotions(input_csv: Path, output_csv: Path) -> None:
    monthly: dict = defaultdict(lambda: {emotion: 0 for emotion in EMOTIONS} | {"total": 0})

    with open(input_csv, "r", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            key = (row["source"], row["period"], row["year_month"])
            emotion = row["emotion"].lower()
            if emotion in monthly[key]:
                monthly[key][emotion] += 1
            monthly[key]["total"] += 1

    results = []
    for (source, period, year_month), data in sorted(monthly.items()):
        total = data["total"] or 1
        entry = {"source": source, "period": period, "year_month": year_month, "sentence_count": data["total"]}
        for emotion in EMOTIONS:
            entry[f"{emotion}_pct"] = round(data[emotion] / total * 100, 2)
        results.append(entry)

    fieldnames = ["source", "period", "year_month", "sentence_count"] + [f"{emotion}_pct" for emotion in EMOTIONS]
    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Emotion summary saved to: {output_csv}")


def summarise_sentiment(input_csv: Path, output_csv: Path, covid_dir: Path = None) -> None:
    monthly_data: dict = defaultdict(lambda: {"scores": [], "labels": [], "confidences": []})

    with open(input_csv, "r", encoding="utf-8") as csv_file:
        for row in csv.DictReader(csv_file):
            key = (row["source"], row["period"], row["year_month"])
            monthly_data[key]["scores"].append(int(row["sentiment_score"]))
            monthly_data[key]["labels"].append(row["sentiment_label"])
            monthly_data[key]["confidences"].append(float(row.get("confidence") or 1.0))

    covid_counts = _count_covid_sentences(covid_dir) if covid_dir and covid_dir.exists() else {}

    monthly_results = []
    for (source, period, year_month), data in sorted(monthly_data.items()):
        scores = data["scores"]
        labels = data["labels"]
        confidences = data["confidences"]
        total = len(labels)
        covid_count = covid_counts.get((source, period, year_month), total)

        total_confidence = sum(confidences)
        weighted_mean = (
            sum(s * c for s, c in zip(scores, confidences)) / total_confidence
            if total_confidence else 0.0
        )

        monthly_results.append({
            "source": source,
            "period": period,
            "year_month": year_month,
            "mean_sentiment": round(mean(scores), 4),
            "weighted_mean_sentiment": round(weighted_mean, 4),
            "median_sentiment": median(scores),
            "positive_pct": round(labels.count("positive") / total * 100, 2),
            "neutral_pct": round(labels.count("neutral") / total * 100, 2),
            "negative_pct": round(labels.count("negative") / total * 100, 2),
            "sentence_count": total,
            "covid_sentence_count": covid_count,
            "sentiment_std": round(stdev(scores), 4) if len(scores) > 1 else 0.0,
        })

    fieldnames = [
        "source", "period", "year_month", "mean_sentiment", "weighted_mean_sentiment",
        "median_sentiment", "positive_pct", "neutral_pct", "negative_pct",
        "sentence_count", "covid_sentence_count", "sentiment_std",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(monthly_results)

    print(f"Monthly summary saved to: {output_csv}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose", "sample"], default="tight")
    parser.add_argument("--model", choices=["altmodel", "vader"], default="altmodel")
    args = parser.parse_args()
    filter_name = args.filter
    model_name = args.model

    covid_dir = PROJECT_ROOT / "data" / "filtered" / "sample" if filter_name == "sample" else None
    summarise_sentiment(
        RESULTS / "csv" / f"sentiment_analysis_details_{filter_name}_{model_name}.csv",
        RESULTS / "csv" / f"sentiment_analysis_monthly_{filter_name}_{model_name}.csv",
        covid_dir=covid_dir,
    )
    # vader doesn't use emotion
    if model_name == "altmodel":
        summarise_emotions(
            RESULTS / "csv" / f"emotion_analysis_details_{filter_name}.csv",
            RESULTS / "csv" / f"emotion_analysis_monthly_{filter_name}.csv",
        )
