# Counts COVID-matching sentences in data/sampled/ per source/period/month.
# Outputs sample_covid_count.csv for use in the dashboard's per-100 metric.

import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "preprocessing"))
from constants import COVID_TERMS

_CURRENT = Path(__file__).resolve()
PROJECT_ROOT = next(p for p in _CURRENT.parents if (p / "data").exists())
RESULTS = _CURRENT.parent.parent / "results"

SAMPLED_DIR = PROJECT_ROOT / "data" / "sampled"

MONTH_MAP = {
    'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
    'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
    'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
}

COVID_REGEX = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in COVID_TERMS) + r")\b",
    re.IGNORECASE,
)


def extract_year_month(filename):
    import re as _re
    year_match = _re.search(r'(\d{4})', filename)
    year = year_match.group(1) if year_match else None
    month = None
    for name, num in MONTH_MAP.items():
        if name in filename.lower():
            month = num
            break
    return year, month


if __name__ == "__main__":
    rows = []
    for txt_file in sorted(SAMPLED_DIR.rglob("*.txt")):
        rel_parts = txt_file.relative_to(SAMPLED_DIR).parts
        source = rel_parts[0] if len(rel_parts) > 1 else "unknown"
        period = rel_parts[1] if len(rel_parts) > 2 else "unknown"
        year_dir = rel_parts[2] if len(rel_parts) > 3 else "unknown"

        year, month = extract_year_month(txt_file.name)
        if not year:
            year = year_dir
        if not month:
            month = "01"

        sentences = [line.strip() for line in txt_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        covid_count = sum(1 for sentence in sentences if COVID_REGEX.search(sentence))
        total = len(sentences)

        rows.append({
            "source": source,
            "period": period,
            "year_month": f"{year}-{month}",
            "total_sampled": total,
            "covid_count": covid_count,
        })

    csv_out = RESULTS / "csv" / "sample_covid_count.csv"
    with open(csv_out, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["source", "period", "year_month", "total_sampled", "covid_count"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Sample COVID counts written to: {csv_out} ({len(rows)} rows)")

    import json
    json_out = RESULTS / "json" / "sample_covid_count.json"
    json_out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"JSON written to: {json_out}")
