import csv
from collections import defaultdict
from statistics import mean, median, stdev


def summarise_sentiment(input_csv, output_csv):
    monthly_data = defaultdict(lambda: {"scores": [], "labels": []})
    
    with open(input_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            year_month = row["year_month"]
            score = int(row["sentiment_score"])
            label = row["sentiment_label"]
            
            monthly_data[year_month]["scores"].append(score)
            monthly_data[year_month]["labels"].append(label)
    
    monthly_results = []
    
    for year_month, data in sorted(monthly_data.items()):
        scores = data["scores"]
        labels = data["labels"]
        
        positive_count = labels.count("positive")
        neutral_count = labels.count("neutral")
        negative_count = labels.count("negative")
        total = len(labels)
        
        sentiment_std = stdev(scores) if len(scores) > 1 else 0.0
        
        monthly_results.append({
            "year_month": year_month,
            "mean_sentiment": round(mean(scores), 4),
            "median_sentiment": median(scores),
            "positive_pct": round(positive_count / total * 100, 2),
            "neutral_pct": round(neutral_count / total * 100, 2),
            "negative_pct": round(negative_count / total * 100, 2),
            "sentence_count": total,
            "sentiment_std": round(sentiment_std, 4)
        })
    
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["year_month", "mean_sentiment", "median_sentiment", "positive_pct", "neutral_pct", "negative_pct", "sentence_count", "sentiment_std"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(monthly_results)
    
    print(f"Monthly summary saved to: {output_csv}")


summarise_sentiment("sentiment_analysis_details_tight_altmodel.csv", "sentiment_analysis_monthly_tight_altmodel.csv")