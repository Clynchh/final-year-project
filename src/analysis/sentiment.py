import re
import csv
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

MODEL_NAME = "siebert/sentiment-roberta-large-english"
BATCH_SIZE = 8  # conservative for CPU — increase if more RAM is available

LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}
SCORE_MAP = {"negative": -1, "neutral": 0, "positive": 1}

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}


def get_sentiment_batch(texts: list[str], tokenizer, model, device) -> list[tuple]:
    inputs = tokenizer(
        texts,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1)
    predicted_classes = torch.argmax(probs, dim=1).tolist()
    confidences = probs[range(len(texts)), predicted_classes].tolist()

    results = []
    for pred_class, confidence in zip(predicted_classes, confidences):
        label = LABEL_MAP[pred_class]
        results.append((label, SCORE_MAP[label], confidence))
    return results


def extract_year_month_from_filename(filename: str) -> tuple[str | None, str | None]:
    year_match = re.search(r'(\d{4})', filename)
    year = year_match.group(1) if year_match else None

    month = None
    filename_lower = filename.lower()
    for month_name, month_num in MONTH_MAP.items():
        if month_name in filename_lower:
            month = month_num
            break

    return year, month


def analyse_sentiment(input_dir: Path, output_csv: Path, tokenizer, model, device) -> None:
    sentence_details = []
    sentence_id = 0

    for txt_file in sorted(input_dir.rglob("*.txt")):
        rel_parts = txt_file.relative_to(input_dir).parts  # (source, period, year, file)
        source = rel_parts[0] if len(rel_parts) > 1 else "unknown"
        period = rel_parts[1] if len(rel_parts) > 2 else "unknown"
        year_dir_name = rel_parts[2] if len(rel_parts) > 3 else "unknown"

        year, month = extract_year_month_from_filename(txt_file.name)
        if not year:
            year = year_dir_name
        if not month:
            month = "01"

        sentences = [s for s in txt_file.read_text(encoding="utf-8").splitlines() if s.strip()]

        for batch_start in range(0, len(sentences), BATCH_SIZE):
            batch = sentences[batch_start: batch_start + BATCH_SIZE]
            results = get_sentiment_batch(batch, tokenizer, model, device)

            for sentence, (label, score, confidence) in zip(batch, results):
                sentence_details.append({
                    "sentence_id": f"{sentence_id:05d}",
                    "year": year,
                    "month": month,
                    "year_month": f"{year}-{month}",
                    "source": source,
                    "period": period,
                    "sentence": sentence,
                    "sentiment_label": label,
                    "sentiment_score": score,
                    "confidence": confidence,
                })
                sentence_id += 1

            if sentence_id % 100 == 0:
                print(f"Processed {sentence_id} sentences...")

    fieldnames = [
        "sentence_id", "year", "month", "year_month", "source", "period",
        "sentence", "sentiment_label", "sentiment_score", "confidence",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentence_details)

    print(f"Sentiment analysis saved to: {output_csv}")
    print(f"Total sentences processed: {sentence_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose", "sample"], default="tight")
    args = parser.parse_args()

    INPUT_DIR = PROJECT_ROOT / "data" / "sampled" if args.filter == "sample" else PROJECT_ROOT / "data" / "filtered" / args.filter
    OUTPUT_CSV = _CURRENT.parent / f"sentiment_analysis_details_{args.filter}_altmodel.csv"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    analyse_sentiment(INPUT_DIR, OUTPUT_CSV, tokenizer, model, device)
