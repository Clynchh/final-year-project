import csv
import json

def convert_csv_to_json(input_csv, output_json):
    data = []
    
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            data.append({
                "year_month": row["year_month"],
                "mean_sentiment": float(row["mean_sentiment"]),
                "median_sentiment": float(row["median_sentiment"]),
                "positive_pct": float(row["positive_pct"]),
                "neutral_pct": float(row["neutral_pct"]),
                "negative_pct": float(row["negative_pct"]),
                "sentence_count": int(row["sentence_count"]),
                "sentiment_std": float(row["sentiment_std"])
            })
    
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Converted {len(data)} rows to {output_json}")


convert_csv_to_json("sentence_count.csv", "sentence_count.json")