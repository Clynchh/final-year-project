# Counts segmented sentences per month across all sources and periods.
# Writes src/results/csv/sentence_count.csv and triggers sentence_count_to_json.py.

import csv
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SEGMENTED    = PROJECT_ROOT / "data" / "segmented"
RESULTS      = PROJECT_ROOT / "src" / "results"

MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]

def main() -> None:
    counts: dict[tuple[str, int], int] = defaultdict(int)

    for source_dir in sorted(SEGMENTED.iterdir()):
        if not source_dir.is_dir():
            continue
        for period_dir in sorted(source_dir.iterdir()):
            if not period_dir.is_dir():
                continue
            for year_dir in sorted(period_dir.iterdir()):
                if not year_dir.is_dir():
                    continue
                for txt in sorted(year_dir.glob("*.txt")):
                    # filename: "Jan 2020.txt"
                    parts = txt.stem.split()
                    if len(parts) != 2 or parts[0] not in MONTH_ABBR:
                        continue
                    month, year = parts[0], int(parts[1])
                    lines = [l for l in txt.read_text(encoding="utf-8").splitlines() if l.strip()]
                    counts[(month, year)] += len(lines)

    # sort by year then month index
    rows = sorted(counts.items(), key=lambda kv: (kv[0][1], MONTH_ABBR.index(kv[0][0])))

    output_csv = RESULTS / "csv" / "sentence_count.csv"
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "year", "count"])
        for (month, year), count in rows:
            writer.writerow([month, year, count])

    print(f"Written {len(rows)} rows to {output_csv}")


if __name__ == "__main__":
    main()
