# VADER lexicon-based sentiment analysis. Outputs same CSV format as polarity_analysis.py.
# VADER gives compound score (-1 to 1); label assigned by standard thresholds.

import csv
import re
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())
RESULTS = _CURRENT.parent.parent / "results"

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}

SCORE_MAP = {"negative": -1, "neutral": 0, "positive": 1}


def classify(compound: float) -> str:
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"


def extract_year_month(filename: str) -> tuple:
    year_match = re.search(r'(\d{4})', filename)
    year = year_match.group(1) if year_match else None
    month = None
    for name, num in MONTH_MAP.items():
        if name in filename.lower():
            month = num
            break
    return year, month


def analyse_vader(input_dir: Path, output_csv: Path) -> None:
    sia = SentimentIntensityAnalyzer()
    rows = []
    sentence_id = 0

    for txt_file in sorted(input_dir.rglob("*.txt")):
        rel_parts = txt_file.relative_to(input_dir).parts
        source = rel_parts[0] if len(rel_parts) > 1 else "unknown"
        period = rel_parts[1] if len(rel_parts) > 2 else "unknown"
        year_dir = rel_parts[2] if len(rel_parts) > 3 else "unknown"

        year, month = extract_year_month(txt_file.name)
        if not year:
            year = year_dir
        if not month:
            month = "01"

        sentences = [s for s in txt_file.read_text(encoding="utf-8").splitlines() if s.strip()]

        for sentence in sentences:
            scores = sia.polarity_scores(sentence)
            compound = scores["compound"]
            label = classify(compound)
            rows.append({
                "sentence_id": f"{sentence_id:05d}",
                "year": year,
                "month": month,
                "year_month": f"{year}-{month}",
                "source": source,
                "period": period,
                "sentence": sentence,
                "sentiment_label": label,
                "sentiment_score": SCORE_MAP[label],
                "confidence": round(abs(compound), 4),
            })
            sentence_id += 1

        if sentence_id % 500 == 0:
            print(f"Processed {sentence_id} sentences...")

    fieldnames = [
        "sentence_id", "year", "month", "year_month", "source", "period",
        "sentence", "sentiment_label", "sentiment_score", "confidence",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"VADER analysis saved to: {output_csv}")
    print(f"Total sentences processed: {sentence_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose", "sample"], default="tight")
    args = parser.parse_args()

    INPUT_DIR = PROJECT_ROOT / "data" / "sampled" if args.filter == "sample" else PROJECT_ROOT / "data" / "filtered" / args.filter
    OUTPUT_CSV = RESULTS / "csv" / f"sentiment_analysis_details_{args.filter}_vader.csv"

    analyse_vader(INPUT_DIR, OUTPUT_CSV)
