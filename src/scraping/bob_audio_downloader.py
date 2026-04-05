# Downloads BoB (Box of Broadcasts) audio month by month via HLS interception + ffmpeg.
# Companion to bob_scraper.py; produces .m4a files for whisper_transcribe.py.

import argparse
import calendar
import re
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from bob_scraper import (  # reuse constants and login helper from the transcript scraper
    COVID_MONTHS,
    CONTROL_MONTHS,
    MONTH_NAMES,
    SESSION_FILE,
    PROJECT_ROOT,
    TIMEOUT_MS,
    _do_login,
    _parse_results,
    _next_page_url,
)

DATA_DIR = PROJECT_ROOT / "data" / "raw"
HLS_TIMEOUT_MS = 60_000  # ms to wait for the HLS playlist to appear

PLAY_SELECTORS = [  # tried in order on BoB programme pages
    "button[class*='play']",
    "button[aria-label*='Play']",
    "button[aria-label*='play']",
    "[data-action='play']",
    "[class*='PlayButton']",
    "[class*='play-button']",
    "button.play",
    ".player button",
    "video",   # clicking the video element itself sometimes starts playback
]


BOB_SEARCH_BASE = "https://learningonscreen.ac.uk/ondemand/search.php/prog"


def search_month_audio(page, year: int, month: int,
                        search_term: str, min_duration: int = 30,
                        debug: bool = False) -> str | None:
    from urllib.parse import urlencode, quote

    last_day = calendar.monthrange(year, month)[1]
    print(f"  Searching: '{search_term}' | {year}-{month:02d}")

    params = {
        "q[0][v]": search_term,
        "search_type": "1",
        "is_available": "",
        "q[0][index]": "title",  # title-only search
        "source": "R",          # radio only
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
    search_url = BOB_SEARCH_BASE + "?" + urlencode(params)

    if debug:
        print(f"  [debug] {search_url}")

    page.goto(search_url)

    try:
        page.wait_for_selector("a[href*='/prog/']", timeout=TIMEOUT_MS)
    except PlaywrightTimeout:
        print("  No results found.")
        return None

    for page_num in range(1, 20):
        raw_items = page.evaluate("""() => {
            const links = document.querySelectorAll('a[href*="/prog/"]');
            const seen = new Set();
            const out = [];
            for (const a of links) {
                if (seen.has(a.href)) continue;
                seen.add(a.href);
                const container = a.closest('li, article, div.result, div.item, tr') || a.parentElement;
                out.push({ href: a.href, text: container ? container.innerText : a.innerText });
            }
            return out;
        }""")

        available_urls = {  # skip items that need a "Request to watch" form
            item['href'] for item in raw_items
            if 'available to watch now' in item['text'].lower()
        }

        if debug:
            print(f"  [page {page_num}] {len(raw_items)} raw, {len(available_urls)} available:")
            for item in raw_items:
                status = "OK" if item['href'] in available_urls else "SKIP (request needed)"
                print(f"    [{status}] {repr(item['text'][:120])}")

        # title_filter omitted: search URL already filters by title, and apostrophe
        # normalisation differences cause false negatives with _parse_results.
        results = [r for r in _parse_results(page) if r['url'] in available_urls]

        if debug:
            print(f"  [page {page_num}] {len(results)} parsed available result(s):")
            for r in results:
                print(f"    {r['year']}-{r['month']:02d} | {r['duration_mins']} min | {r['url']}")

        match = next(
            (r for r in results
             if r['year'] == year and r['month'] == month
             and r['duration_mins'] is not None and r['duration_mins'] >= min_duration),
            None
        )
        if match:
            print(f"  Found on page {page_num}: {match['duration_mins']} min → {match['url']}")
            return match['url']

        next_url = _next_page_url(page)
        if not next_url:
            break

        if debug:
            print(f"  No match on page {page_num}, trying next page...")
        page.goto(next_url)
        page.wait_for_load_state("domcontentloaded")

    print(f"  No result >= {min_duration} min found.")
    return None


def _derive_playlist_url(segment_url: str) -> str | None:
    # BoB CDN pattern: .../Name.m4a/segment-N-a1.ts → .../Name.m4a/index.m3u8
    m = re.search(r'(https?://cdn\.learningonscreen\.ac\.uk/hls/[^?#]+\.m4a)/', segment_url)
    if m:
        return m.group(1) + "/index.m3u8"
    return None


def intercept_hls(page, prog_url: str, debug: bool = False) -> str | None:
    playlist_url = None
    segment_url = None  # fallback: derive playlist URL from an intercepted .ts segment

    def handle_request(request):
        nonlocal playlist_url, segment_url
        url = request.url
        if "cdn.learningonscreen.ac.uk/hls" not in url:
            return
        if debug:
            print(f"    [hls req] {url[:120]}")
        if ".m3u8" in url and playlist_url is None:
            playlist_url = url
        elif ".ts" in url and segment_url is None:
            segment_url = url

    page.on("request", handle_request)
    page.goto(prog_url)
    page.wait_for_load_state("domcontentloaded")
    time.sleep(1)

    # Try clicking a play button
    clicked = False
    for sel in PLAY_SELECTORS:
        try:
            page.click(sel, timeout=3_000)
            print(f"    Clicked play via: {sel}")
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        print("    Could not find play button automatically.")
        print("    >>> Please click Play in the browser window <<<")

    deadline = time.time() + HLS_TIMEOUT_MS / 1000
    while playlist_url is None and time.time() < deadline:
        if segment_url:
            derived = _derive_playlist_url(segment_url)  # derive playlist from first segment seen
            if derived:
                print(f"    Derived playlist from segment: {derived[:100]}")
                playlist_url = derived
                break
        page.wait_for_timeout(300)

    page.remove_listener("request", handle_request)
    return playlist_url


# ---------------------------------------------------------------------------
# ffmpeg download
# ---------------------------------------------------------------------------

def download_audio(playlist_url: str, output_path: Path,
                   cookies: list[dict] | None = None) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp.m4a")

    headers = ""  # optional Cookie header forwarded to ffmpeg
    if cookies:
        cookie_str = "; ".join(
            f"{c['name']}={c['value']}"
            for c in cookies
            if "learningonscreen.ac.uk" in c.get("domain", "")
               or "cdn.learningonscreen.ac.uk" in c.get("domain", "")
        )
        if cookie_str:
            headers = f"Cookie: {cookie_str}\r\n"

    cmd = ["ffmpeg", "-y"]
    if headers:
        cmd += ["-headers", headers]
    cmd += [
        "-i", playlist_url,
        "-vn",            # audio only
        "-acodec", "copy",
        str(tmp_path),
    ]

    print(f"    Downloading via ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"    ERROR: ffmpeg failed:")
        print(result.stderr[-1000:])
        if tmp_path.exists():
            tmp_path.unlink()
        return False

    tmp_path.rename(output_path)
    size_mb = output_path.stat().st_size / 1_048_576
    print(f"    Saved {size_mb:.1f} MB → {output_path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download BoB audio month-by-month and save as .m4a"
    )
    parser.add_argument(
        "--period", choices=["covid", "control"], required=True,
    )
    parser.add_argument(
        "--source", default="bbc_radio4",
        help="Output name under data/raw/ (default: bbc_radio4)"
    )
    parser.add_argument(
        "--search", default="Six O'Clock News",
        help="Programme title to search for on BoB (default: \"Six O'Clock News\")"
    )
    parser.add_argument(
        "--min-duration", type=int, default=30, dest="min_duration",
        help="Minimum episode duration in minutes (default: 30)"
    )
    parser.add_argument(
        "--only", metavar="YYYY-MM",
        help="Download a single month only"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-download months that already have an .m4a file"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Find programme URLs but do not download audio"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Print HLS request URLs and extra diagnostic info"
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

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        if SESSION_FILE.exists():
            context = browser.new_context(storage_state=str(SESSION_FILE))
            page = context.new_page()
            page.goto("https://learningonscreen.ac.uk/ondemand/")
            page.wait_for_load_state("domcontentloaded")
            if "login" in page.url or "shibboleth" in page.url.lower():
                print("Saved session expired — please log in again.")
                SESSION_FILE.unlink()
                context.close()
                context = browser.new_context()
                page = context.new_page()
                _do_login(page)
                context.storage_state(path=str(SESSION_FILE))
            else:
                print("Loaded saved session — no login needed.")
        else:
            context = browser.new_context()
            page = context.new_page()
            _do_login(page)
            context.storage_state(path=str(SESSION_FILE))
            print("Session saved.")

        for year, month in months:
            month_name = MONTH_NAMES[month]
            month_label = f"{month_name} {year}"
            out_path = (DATA_DIR / args.source / args.period
                        / str(year) / f"{month_name} {year}.m4a")

            if out_path.exists() and out_path.stat().st_size > 0 and not args.overwrite:
                print(f"[SKIP] {month_label} — already downloaded")
                continue

            print(f"\n[{month_label}]")

            chosen_url = search_month_audio(
                page, year, month,
                search_term=args.search,
                min_duration=args.min_duration,
                debug=args.debug,
            )

            if not chosen_url:
                print(f"  No results — skipping")
                continue

            print(f"  Programme page: {chosen_url}")

            if args.dry_run:
                print(f"  [dry-run] Would save to: {out_path.relative_to(PROJECT_ROOT)}")
                continue

            playlist = intercept_hls(page, chosen_url, debug=args.debug)
            context.storage_state(path=str(SESSION_FILE))  # keep session fresh

            if not playlist:
                print(f"  ERROR: could not intercept HLS playlist — skipping")
                print(f"  Try clicking play manually within the {HLS_TIMEOUT_MS//1000}s window")
                continue

            cookies = context.cookies()
            download_audio(playlist, out_path, cookies=cookies)

        browser.close()
        print("\nDone.")


if __name__ == "__main__":
    main()
