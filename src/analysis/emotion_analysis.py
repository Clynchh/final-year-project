# Emotion analysis using j-hartmann/emotion-english-distilroberta-base.
# Runs on tight-filtered sentences and outputs per-sentence emotion labels + confidence.

import csv
from pathlib import Path
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())

MODEL_NAME = "j-hartmann/emotion-english-distilroberta-base"
BATCH_SIZE = 8

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}


def get_emotion_batch(texts: list[str], tokenizer, model, device, id2label: dict) -> list[tuple]:
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
    predicted = torch.argmax(probs, dim=1).tolist()
    confidences = probs[range(len(texts)), predicted].tolist()

    return [
        (id2label[pred], confidences[i])
        for i, pred in enumerate(predicted)
    ]


def extract_year_month(filename: str) -> tuple[str | None, str | None]:
    import re
    year_match = re.search(r'(\d{4})', filename)
    year = year_match.group(1) if year_match else None
    month = next(
        (num for name, num in MONTH_MAP.items() if name in filename.lower()),
        None
    )
    return year, month


def analyse_emotions(input_dir: Path, output_csv: Path, tokenizer, model, device, id2label) -> None:
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

        for batch_start in range(0, len(sentences), BATCH_SIZE):
            batch = sentences[batch_start: batch_start + BATCH_SIZE]
            results = get_emotion_batch(batch, tokenizer, model, device, id2label)

            for sentence, (emotion, confidence) in zip(batch, results):
                rows.append({
                    "sentence_id": f"{sentence_id:05d}",
                    "year": year,
                    "month": month,
                    "year_month": f"{year}-{month}",
                    "source": source,
                    "period": period,
                    "sentence": sentence,
                    "emotion": emotion,
                    "confidence": round(confidence, 6),
                })
                sentence_id += 1

        if sentence_id % 100 == 0:
            print(f"  Processed {sentence_id} sentences...")

    fieldnames = [
        "sentence_id", "year", "month", "year_month", "source", "period",
        "sentence", "emotion", "confidence",
    ]
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Emotion analysis saved to: {output_csv}")
    print(f"Total sentences processed: {sentence_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--filter", choices=["tight", "loose"], default="tight")
    args = parser.parse_args()

    INPUT_DIR = PROJECT_ROOT / "data" / "filtered" / args.filter
    OUTPUT_CSV = _CURRENT.parent / f"emotion_analysis_details_{args.filter}.csv"

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    id2label = model.config.id2label
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    analyse_emotions(INPUT_DIR, OUTPUT_CSV, tokenizer, model, device, id2label)
