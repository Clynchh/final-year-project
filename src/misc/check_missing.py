# Reports missing or empty transcript files across all sources and periods.
# Compares expected months against what exists in data/raw/.

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW = PROJECT_ROOT / "data" / "raw"

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

COVID_MONTHS = [
    (y, m) for y in range(2019, 2024)
    for m in range(1, 13)
    if (2019, 12) <= (y, m) <= (2023, 5)
]

CONTROL_MONTHS = [
    (y, m) for y in range(2016, 2020)
    for m in range(1, 13)
    if (2016, 6) <= (y, m) <= (2019, 11)
]

SOURCES = [
    "bbc_news_tv",
    "bbc_radio4",
    "graham_norton",
    "qi",
    "the_last_leg",
    "the_one_show",
]

PERIODS = {
    "covid": COVID_MONTHS,
    "control": CONTROL_MONTHS,
}


def check():
    any_issues = False
    for source in SOURCES:
        for period, months in PERIODS.items():
            missing = []
            empty = []
            for year, month in months:
                month_name = MONTH_NAMES[month - 1]
                txt = RAW / source / period / str(year) / f"{month_name} {year}.txt"
                if not txt.exists():
                    missing.append(f"{month_name} {year}")
                elif txt.stat().st_size == 0:
                    empty.append(f"{month_name} {year}")

            if missing or empty:
                any_issues = True
                print(f"\n{source}/{period}:")
                if missing:
                    print(f"  MISSING ({len(missing)}): {', '.join(missing)}")
                if empty:
                    print(f"  EMPTY   ({len(empty)}): {', '.join(empty)}")

    if not any_issues:
        print("All expected transcript files are present and non-empty.")


if __name__ == "__main__":
    check()
