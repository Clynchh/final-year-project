# Scrapes BoB (Box of Broadcasts) transcripts for BBC News month by month.
# Saves combined text to data/raw/. Use --period covid|control, --only YYYY-MM to rerun gaps.

import argparse
import calendar
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

BOB_URL = "https://learningonscreen.ac.uk/ondemand/"
SEARCH_TERM = "BBC News"

PAGE_DELAY = 2      # seconds between page actions
TIMEOUT_MS = 15_000  # ms to wait for a page element to appear

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
SESSION_FILE = PROJECT_ROOT / "bob_session.json"

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

COVID_MONTHS = [  # inclusive month ranges
    (y, m) for y in range(2019, 2024)
    for m in range(1, 13)
    if (2019, 12) <= (y, m) <= (2023, 5)
]

CONTROL_MONTHS = [
    (y, m) for y in range(2016, 2020)
    for m in range(1, 13)
    if (2016, 6) <= (y, m) <= (2019, 11)
]


def month_date_range(year: int, month: int) -> tuple[str, str]:
    last_day = calendar.monthrange(year, month)[1]
    return f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last_day:02d}"


def output_path(source: str, period: str, year: int, month: int) -> Path:
    month_name = MONTH_NAMES[month]
    path = DATA_DIR / source / period / str(year)
    path.mkdir(parents=True, exist_ok=True)
    return path / f"{month_name} {year}.txt"


def already_scraped(source: str, period: str, year: int, month: int) -> bool:
    p = output_path(source, period, year, month)
    return p.exists() and p.stat().st_size > 0


MONTH_ABBR = {
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
    'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
}


def _parse_results(page, title_filter: str = "") -> list[dict]:
    items = page.evaluate("""() => {
        const links = document.querySelectorAll('a[href*="/prog/"]');
        const seen = new Set();
        const results = [];
        for (const a of links) {
            if (seen.has(a.href)) continue;
            seen.add(a.href);
            const container = a.closest('li, article, div.result, div.item, tr') || a.parentElement;
            results.push({ href: a.href, text: container ? container.innerText : a.innerText });
        }
        return results;
    }""")

    parsed = []
    for item in items:
        text = item['text']

        date_match = re.search(  # "15 January 2020" or "15 Jan 2020"
            r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})',
            text, re.IGNORECASE
        )
        if not date_match:
            continue
        item_month = MONTH_ABBR.get(date_match.group(2).lower()[:3])
        item_year = int(date_match.group(3))

        duration_mins = None  # parsed from "(120 mins)" or "(2:30:00)" or "(2h 30m)"
        m = re.search(r'\((\d+)\s*mins?\)', text, re.IGNORECASE)
        if m:
            duration_mins = int(m.group(1))
        else:
            m = re.search(r'\((\d+):(\d{2}):\d{2}\)', text)
            if m:
                duration_mins = int(m.group(1)) * 60 + int(m.group(2))
            else:
                m = re.search(r'\((\d+)h\s*(\d+)?m?\)', text, re.IGNORECASE)
                if m:
                    duration_mins = int(m.group(1)) * 60 + int(m.group(2) or 0)

        if title_filter and title_filter.lower() not in item['text'].lower():
            continue

        parsed.append({
            'url': item['href'],
            'year': item_year,
            'month': item_month,
            'duration_mins': duration_mins,
        })

    return parsed


PREFER_MINUTES  = 180   # prefer episodes >= 3 hours
FALLBACK_MINUTES = 120  # accept >= 2 hours if nothing longer found
MAX_PAGES = 20           # safety cap on pagination


def _next_page_url(page) -> str | None:
    next_selectors = [
        "a[rel='next']",
        "a.next",
        "a:has-text('Next')",
        "a:has-text('>')",
        "[class*='pagination'] a:has-text('Next')",
        "[class*='pager'] a:has-text('Next')",
    ]
    for selector in next_selectors:
        try:
            el = page.query_selector(selector)
            if el:
                href = el.get_attribute("href")
                if href:
                    return href
        except Exception:
            continue
    return None


def _pick_from_results(results: list[dict], year: int, month: int,
                       min_duration: int | None = None) -> tuple[list[str], list[str]]:
    # Returns (preferred_urls, fallback_urls); min_duration overrides the default 180/120 thresholds.
    in_month = [
        r for r in results
        if r['year'] == year and r['month'] == month and r['duration_mins'] is not None
    ]
    if min_duration is not None:
        matched = [r['url'] for r in in_month if r['duration_mins'] >= min_duration]
        return matched, matched
    preferred = [r['url'] for r in in_month if r['duration_mins'] >= PREFER_MINUTES]
    fallback  = [r['url'] for r in in_month if r['duration_mins'] >= FALLBACK_MINUTES]
    return preferred, fallback


BOB_SEARCH_BASE = "https://learningonscreen.ac.uk/ondemand/search.php/prog"


def search_month(page, year: int, month: int, search_term: str = "BBC News",
                 title_filter: str = "", min_duration: int | None = None,
                 title_only: bool = False, media_type: str = "",
                 debug: bool = False) -> list[str]:
    from urllib.parse import urlencode
    last_day = calendar.monthrange(year, month)[1]
    print(f"  Searching: '{search_term}' | {year}-{month:02d}", end="")
    if title_filter:
        print(f" | title contains '{title_filter}'", end="")
    print()

    if title_only:
        params = {
            "q[0][v]": search_term,
            "search_type": "1",
            "is_available": "",
            "q[0][index]": "title",
            "source": media_type,  # "" = all, "R" = radio, "T" = TV
            "genre": "",
            "date_type": "1",
            "date_start[0]": str(year),
            "date_start[1]": f"{month:02d}",
            "date_start[2]": "01",
            "date_start[3]": "00",
            "date_start[4]": "00",
            "date_end[0]": str(year),
            "date_end[1]": f"{month:02d}",
            "date_end[2]": str(last_day),
            "date_end[3]": "23",
            "date_end[4]": "59",
            "institution": "",
            "subject_id": "",
            "sort": "relevance",
        }
        page.goto(BOB_SEARCH_BASE + "?" + urlencode(params))
    else:
        page.goto(BOB_URL)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(PAGE_DELAY)

        page.click("#header-search-button")
        time.sleep(0.5)
        page.fill('input[id="q[0][v]"]', search_term)

        # Set date filter and sort via JS — hidden elements can't be clicked directly
        page.evaluate(f"""() => {{
            const radio = document.querySelector('#search_date_custom');
            if (radio) {{
                radio.checked = true;
                radio.dispatchEvent(new Event('change', {{bubbles: true}}));
                radio.dispatchEvent(new Event('click',  {{bubbles: true}}));
            }}
            const startYear  = document.querySelectorAll('select[name="date_start[0]"]')[0];
            const startMonth = document.querySelectorAll('select[name="date_start[1]"]')[0];
            const startDay   = document.querySelectorAll('select[name="date_start[2]"]')[0];
            const endYear    = document.querySelectorAll('select[name="date_end[0]"]')[0];
            const endMonth   = document.querySelectorAll('select[name="date_end[1]"]')[0];
            const endDay     = document.querySelectorAll('select[name="date_end[2]"]')[0];
            if (startYear)  startYear.value  = '{year}';
            if (startMonth) startMonth.value = '{month:02d}';
            if (startDay)   startDay.value   = '01';
            if (endYear)    endYear.value    = '{year}';
            if (endMonth)   endMonth.value   = '{month:02d}';
            if (endDay)     endDay.value     = '{last_day:02d}';
            const sort = document.querySelector('select#sort, select[name="sort"]');
            if (sort) sort.value = 'date';
        }}""")
        time.sleep(0.3)
        page.click("#submit")

    try:
        page.wait_for_selector("a[href*='/prog/']", timeout=TIMEOUT_MS)
    except PlaywrightTimeout:
        print("  No results found.")
        return []

    all_preferred: list[str] = []
    all_fallback: list[str] = []

    for page_num in range(1, MAX_PAGES + 1):
        if debug:
            print(f"  [page {page_num}] {page.url}")

        results = _parse_results(page, title_filter=title_filter)

        if debug:
            for r in results:
                print(f"    {r['year']}-{r['month']:02d} | {r['duration_mins']} min | {r['url']}")

        preferred, fallback = _pick_from_results(results, year, month, min_duration=min_duration)
        all_preferred.extend(preferred)
        all_fallback.extend(fallback)

        next_url = _next_page_url(page)
        if not next_url:
            break  # no more pages

        page.goto(next_url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(PAGE_DELAY)

    if all_preferred:
        print(f"  Found {len(all_preferred)} candidate(s) >= {PREFER_MINUTES} min.")
        return all_preferred

    if all_fallback:
        print(f"  No {PREFER_MINUTES}+ min result; using {len(all_fallback)} fallback candidate(s) >= {FALLBACK_MINUTES} min.")
        return all_fallback

    print(f"  No results matched {year}-{month:02d} >= {FALLBACK_MINUTES} min across all pages.")
    return []


def get_broadcast_date(page) -> tuple[int, int] | None:
    date_text = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.children.length > 0) continue;
            const t = (el.innerText || el.textContent || '').trim();
            // Match "15 January 2020", "Jan 2020", or "2020-01-15"
            if (/\\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{4}\\b/i.test(t)) return t;
            if (/\\b\\d{1,2}\\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{4}\\b/i.test(t)) return t;
            if (/\\b20\\d{2}-\\d{2}-\\d{2}\\b/.test(t)) return t;
        }
        return null;
    }""")

    if not date_text:
        return None

    MONTH_ABBR = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12,
    }

    m = re.search(r'(20\d{2})-(\d{2})-\d{2}', date_text)  # YYYY-MM-DD
    if m:
        return int(m.group(1)), int(m.group(2))

    m = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(20\d{2})', date_text, re.IGNORECASE)  # "15 January 2020" or "January 2020"
    if m:
        month = MONTH_ABBR.get(m.group(1).lower()[:3])
        return int(m.group(2)), month

    return None


def get_duration_minutes(page) -> int | None:
    duration_text = page.evaluate("""() => {
        const all = document.querySelectorAll('*');
        for (const el of all) {
            if (el.children.length > 0) continue;  // leaf nodes only
            const t = el.innerText || el.textContent || '';
            // match H:MM:SS, Xh Ym, or "X mins"
            if (/\\d+:\\d{2}:\\d{2}/.test(t) || /\\d+h\\s*\\d+m/.test(t) || /\\d+ mins?/i.test(t)) {
                return t.trim();
            }
        }
        return null;
    }""")

    if not duration_text:
        return None

    m = re.search(r'(\d+):(\d{2}):(\d{2})', duration_text)  # HH:MM:SS
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r'(\d+):(\d{2})$', duration_text)  # H:MM
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.search(r'(\d+)h\s*(\d+)?m?', duration_text)  # Xh Ym
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    m = re.search(r'(\d+)\s*min', duration_text, re.IGNORECASE)  # X mins
    if m:
        return int(m.group(1))

    return None


def extract_transcript(page, url: str, debug: bool = False, already_loaded: bool = False) -> tuple[str, str]:
    if not already_loaded:
        page.goto(url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(PAGE_DELAY)

    citation = _extract_citation(page, debug)  # grab citation before clicking anything

    transcript_btn_selectors = [
        "button:has-text('transcript')",
        "button:has-text('Transcript')",
        "a:has-text('transcript')",
        "a:has-text('Transcript')",
        "[data-action='transcript']",
    ]

    clicked = False
    for selector in transcript_btn_selectors:
        try:
            page.click(selector, timeout=5_000)
            clicked = True
            break
        except PlaywrightTimeout:
            continue

    if not clicked:
        print(f"  WARNING: Could not find transcript button on {url}")
        if debug:
            print("  Buttons found on page:")
            btns = page.evaluate("() => Array.from(document.querySelectorAll('button, a')).map(e => e.outerHTML.slice(0,120))")
            for b in btns[:30]:
                print("   ", b)
        return "", citation

    time.sleep(PAGE_DELAY)

    if debug:
        print("\n--- DEBUG: after clicking transcript button ---")
        _debug_page_elements(page)

    transcript_selectors = [
        "#transcript",
        ".transcript",
        "[class*='transcript']",
        "[id*='transcript']",
        ".captions",
        "#captions",
    ]

    for selector in transcript_selectors:
        try:
            el = page.wait_for_selector(selector, timeout=5_000)
            if el:
                text = el.inner_text()
                if text.strip():
                    return text.strip(), citation
        except PlaywrightTimeout:
            continue

    print(f"  WARNING: Could not locate transcript container on {url}")
    print("  Run with --debug to inspect the page and find the right selector.")
    return "", citation


def _extract_citation(page, debug: bool = False) -> str:
    citation_selectors = [
        "[class*='citation']",
        "[id*='citation']",
        "[class*='cite']",
        "[id*='cite']",
        "[class*='reference']",
        "[id*='reference']",
        "button:has-text('Cite')",
        "a:has-text('Cite')",
    ]

    # Some BoB pages need the citation button clicked to reveal the text
    for selector in citation_selectors:
        try:
            page.click(selector, timeout=3_000)
            time.sleep(0.5)
            break
        except PlaywrightTimeout:
            continue

    for selector in citation_selectors:
        try:
            el = page.query_selector(selector)
            if el:
                text = el.inner_text().strip()
                text = re.sub(r'\bCOPY TEXT\b', '', text, flags=re.IGNORECASE).strip()  # strip BoB UI artefact
                if text and len(text) > 10:
                    return text
        except Exception:
            continue

    if debug:
        print("\n--- DEBUG: citation not found — all buttons/links on page ---")
        btns = page.evaluate("""() =>
            Array.from(document.querySelectorAll('button, a')).map(e => e.outerHTML.slice(0, 120))
        """)
        for b in btns[:40]:
            print("  ", b)

    return ""


def _debug_page_elements(page) -> None:
    info = page.evaluate("""() => {
        const els = document.querySelectorAll('[id], [class]');
        return Array.from(els).slice(0, 100).map(e =>
            `<${e.tagName.toLowerCase()} id="${e.id}" class="${e.className}">`
        );
    }""")
    for line in info:
        print(line)

    inputs = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('input, select')).map(e =>
            `<${e.tagName.toLowerCase()} id="${e.id}" name="${e.name}" type="${e.type}" placeholder="${e.placeholder}">`
        );
    }""")
    print("\n--- All inputs/selects ---")
    for line in inputs:
        print(line)
    print("----------------------------\n")


def _do_login(page) -> None:
    page.goto("https://learningonscreen.ac.uk/ondemand/")
    print("\n" + "="*60)
    print("Please log in with your university credentials in the")
    print("browser window, then come back here and press Enter.")
    print("="*60)
    input()


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape BoB transcripts")
    parser.add_argument(
        "--period", choices=["covid", "control"], required=True,
        help="Which date range to scrape"
    )
    parser.add_argument(
        "--only", metavar="YYYY-MM",
        help="Scrape a single month only (e.g. 2020-03)"
    )
    parser.add_argument(
        "--from", metavar="YYYY-MM", dest="from_month",
        help="Skip all months before this one (e.g. 2017-03)"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Print page element info to help identify selectors"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-scrape months that already have data"
    )
    parser.add_argument(
        "--source", default="bbc_news_tv",
        help="Output directory name under data/raw/ (default: bbc_news_tv)"
    )
    parser.add_argument(
        "--search", default="BBC News",
        help="Search term to use on BoB (default: 'BBC News')"
    )
    parser.add_argument(
        "--title-filter", default="",
        dest="title_filter",
        help="Only accept results whose title contains this string (case-insensitive)"
    )
    parser.add_argument(
        "--min-duration", type=int, default=None,
        dest="min_duration",
        help="Minimum duration in minutes to accept (overrides default 180/120 thresholds)"
    )
    parser.add_argument(
        "--title-only", action="store_true", dest="title_only",
        help="Search by title field only (more precise results)"
    )
    parser.add_argument(
        "--media-type", default="", dest="media_type",
        choices=["", "R", "T"],
        help="Filter by media type: '' = all (default), 'R' = radio, 'T' = TV"
    )
    args = parser.parse_args()

    months = COVID_MONTHS if args.period == "covid" else CONTROL_MONTHS

    if args.only:
        try:
            y, m = map(int, args.only.split("-"))
            months = [(y, m)]
        except ValueError:
            print("--only must be in YYYY-MM format")
            sys.exit(1)

    if args.from_month:
        try:
            fy, fm = map(int, args.from_month.split("-"))
            months = [(y, m) for y, m in months if (y, m) >= (fy, fm)]
        except ValueError:
            print("--from must be in YYYY-MM format")
            sys.exit(1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        # Load saved session if it exists, otherwise prompt for login
        if SESSION_FILE.exists():
            context = browser.new_context(storage_state=str(SESSION_FILE))
            page = context.new_page()
            page.goto("https://learningonscreen.ac.uk/ondemand/")
            page.wait_for_load_state("domcontentloaded")
            if "login" in page.url or "shibboleth" in page.url.lower():  # session expired check
                print("Saved session has expired — please log in again.")
                SESSION_FILE.unlink()
                context.close()
                context = browser.new_context()
                page = context.new_page()
                _do_login(page)
                context.storage_state(path=str(SESSION_FILE))
                print("Session saved.")
            else:
                print("Loaded saved session — no login needed.")
        else:
            context = browser.new_context()
            page = context.new_page()
            _do_login(page)
            context.storage_state(path=str(SESSION_FILE))
            print("Session saved for future runs.")

        for year, month in months:
            month_label = f"{MONTH_NAMES[month]} {year}"

            if not args.overwrite and not args.debug and already_scraped(args.source, args.period, year, month):  # --debug forces re-scrape
                print(f"[SKIP] {month_label} — already scraped")
                continue

            print(f"\n[{month_label}]")

            urls = search_month(page, year, month,
                               search_term=args.search,
                               title_filter=args.title_filter,
                               min_duration=args.min_duration,
                               title_only=args.title_only,
                               media_type=args.media_type,
                               debug=args.debug)

            if not urls:
                print(f"  No results found — skipping")
                continue

            transcript, citation, chosen_url = "", "", ""
            for candidate_url in urls:
                print(f"  Trying: {candidate_url}")
                transcript, citation = extract_transcript(page, candidate_url, debug=args.debug)
                if transcript:
                    chosen_url = candidate_url
                    break
                print(f"  No transcript on this page — trying next candidate...")

            if transcript:
                content = transcript
                if citation:
                    content += f"\n\n---\n{citation}"
                out = output_path(args.source, args.period, year, month)
                out.write_text(content, encoding="utf-8")
                print(f"  Saved {len(transcript):,} chars → {out.relative_to(PROJECT_ROOT)}")
                if citation:
                    print(f"  Citation appended.")
                else:
                    print(f"  WARNING: No citation found — check page manually.")
            else:
                print(f"  No transcript found in any candidate for {month_label}")

        browser.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
