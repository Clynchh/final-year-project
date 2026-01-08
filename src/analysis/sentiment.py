import os
import re
import csv
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

MODEL_NAME = "siebert/sentiment-roberta-large-english"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

LABEL_MAP = {0: "negative", 1: "neutral", 2: "positive"}
SCORE_MAP = {"negative": -1, "neutral": 0, "positive": 1}

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
}


def get_sentiment(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = torch.softmax(outputs.logits, dim=1)
    predicted_class = torch.argmax(probs, dim=1).item()
    confidence = probs[0][predicted_class].item()
    
    label = LABEL_MAP[predicted_class]
    score = SCORE_MAP[label]
    
    return label, score, confidence


def extract_year_month_from_filename(filename):
    filename_lower = filename.lower()
    
    year_match = re.search(r'(\d{4})', filename)
    year = year_match.group(1) if year_match else None
    
    month = None
    for month_name, month_num in MONTH_MAP.items():
        if month_name in filename_lower:
            month = month_num
            break
    
    return year, month


def analyse_sentiment(input_dir, output_csv):
    sentence_details = []
    sentence_id = 0
    
    for year_dir in sorted(os.listdir(input_dir)):
        year_path = os.path.join(input_dir, year_dir)
        
        if not os.path.isdir(year_path):
            continue
        
        for filename in sorted(os.listdir(year_path)):
            if not filename.lower().endswith(".txt"):
                continue
            
            file_path = os.path.join(year_path, filename)
            
            year, month = extract_year_month_from_filename(filename)
            
            if not year:
                year = year_dir
            if not month:
                month = "01"
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            sentences = [s.strip() for s in content.split('\n') if s.strip()]
            
            for sentence in sentences:
                label, score, confidence = get_sentiment(sentence)
                
                sentence_details.append({
                    "sentence_id": f"{sentence_id:05d}",
                    "year": year,
                    "month": month,
                    "year_month": f"{year}-{month}",
                    "source": "BBC News TV",
                    "sentence": sentence,
                    "sentiment_label": label,
                    "sentiment_score": score,
                    "confidence": confidence
                })
                
                sentence_id += 1
                
                if sentence_id % 100 == 0:
                    print(f"Processed {sentence_id} sentences...")
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["sentence_id", "year", "month", "year_month", "source", "sentence", "sentiment_label", "sentiment_score", "confidence"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sentence_details)
    
    print(f"Sentiment analysis saved to: {output_csv}")
    print(f"Total sentences processed: {sentence_id}")


INPUT_DIR = "../../data/filtered/tight/BBC News TV"
OUTPUT_CSV = "sentiment_analysis_details_tight_altmodel.csv"

analyse_sentiment(INPUT_DIR, OUTPUT_CSV)