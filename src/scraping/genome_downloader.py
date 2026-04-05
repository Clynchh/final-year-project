# Bulk-downloads one BBC Sounds episode per month via Genome search + DASH interception + ffmpeg.
# Uses the same approach as bbc_sounds_downloader.py but driven by Genome search results.

import argparse
import calendar
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "raw"
SESSION_FILE = PROJECT_ROOT / "bbc_sounds_session.json"

GENOME_BASE = "https://genome.ch.bbc.co.uk/search"
SOUNDS_BASE = "https://www.bbc.co.uk/sounds/play/"

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}

COVID_MONTHS = [  # Dec 2019 – May 2023
    (2019, 12),
    *[(y, m) for y in range(2020, 2023) for m in range(1, 13)],
    *[(2023, m) for m in range(1, 6)],
]

CONTROL_MONTHS = [  # Jun 2017 – Nov 2019
    *[(2017, m) for m in range(6, 13)],
    *[(y, m) for y in range(2018, 2019) for m in range(1, 13)],
    *[(2019, m) for m in range(1, 12)],
]

MANIFEST_TIMEOUT_MS = 60_000


def _genome_search_url(programme: str, service: str, year: int, month: int,
                        offset: int = 0, limit: int = 20) -> str:
    last_day = calendar.monthrange(year, month)[1]
    params = {
        "q": programme,
        "services": service,
        "from": f"{year}-{month:02d}-01",
        "to": f"{year}-{month:02d}-{last_day}",
        "playable": "1",
    }
    return f"{GENOME_BASE}/{offset}/{limit}?{urlencode(params)}"


def _parse_genome_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []

    for tag in soup.find_all("a", href=re.compile(r"/sounds/play/\w+")):
        sounds_url = "https://www.bbc.co.uk" + tag["href"] if tag["href"].startswith("/") else tag["href"]

        # Walk up to find the containing block that has the title / date info
        container = tag
        for _ in range(6):
            container = container.parent
            if container is None:
                break
            text = container.get_text(" ", strip=True)
            if len(text) > 20:
                break

        title = ""
        date_str = ""
        if container:
            text = container.get_text(" ", strip=True)
            date_match = re.search(  # "01 Dec 2019" or "2019-12-01"
                r"\b(\d{1,2}\s+\w+\s+\d{4}|\d{4}-\d{2}-\d{2})\b", text
            )
            if date_match:
                date_str = date_match.group(1)
            title = text[:80]

        results.append({
            "title": title,
            "date_str": date_str,
            "sounds_url": sounds_url,
        })

    return results


def find_episode_for_month(programme: str, service: str,
                            year: int, month: int,
                            debug: bool = False) -> str | None:
    session = requests.Session()
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    offset = 0
    limit = 20
    seen_urls: set[str] = set()

    while True:
        url = _genome_search_url(programme, service, year, month, offset, limit)
        if debug:
            print(f"    [genome] {url}")

        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  Genome request failed: {e}")
            return None

        results = _parse_genome_page(resp.text)
        if debug:
            print(f"    [genome] {len(results)} results on this page")
            for r in results:
                print(f"      {r['date_str']:20s}  {r['sounds_url']}")

        new_results = [r for r in results if r["sounds_url"] not in seen_urls]
        if not new_results:
            break  # no more pages

        for r in new_results:
            seen_urls.add(r["sounds_url"])

        if new_results:
            return new_results[0]["sounds_url"]  # take the earliest episode of the month

        offset += limit

    return None


def intercept_manifest(page, sounds_url: str) -> str | None:
    manifest_url = None

    def handle_request(request):
        nonlocal manifest_url
        if ".mpd" in request.url and manifest_url is None:
            print(f"  [manifest] {request.url[:100]}")
            manifest_url = request.url

    page.on("request", handle_request)
    page.goto(sounds_url)

    try:
        page.wait_for_load_state("networkidle", timeout=30_000)  # wait for login/consent to settle
    except Exception:
        pass

    PLAY_SELECTORS = [
        "[data-testid='play-button']",
        "[data-testid='hero-play-button']",
        "button[aria-label='Play']",
        "button[aria-label*='Play']",
        "button[title*='Play']",
        "[class*='play-button']",
        "[class*='PlayButton']",
        "button.sc-c-play-pause-button",
    ]
    clicked = False
    for sel in PLAY_SELECTORS:
        try:
            page.click(sel, timeout=3_000)
            print(f"  Clicked play via: {sel}")
            clicked = True
            break
        except Exception:
            continue

    if not clicked:
        print("  Could not find play button automatically.")
        print("  >>> Please click Play in the browser window <<<")

    deadline = time.time() + MANIFEST_TIMEOUT_MS / 1000
    while manifest_url is None and time.time() < deadline:
        page.wait_for_timeout(300)

    page.remove_listener("request", handle_request)
    return manifest_url


def download_audio(manifest_url: str, output_path: Path) -> bool:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(".tmp.m4a")

    cmd = [
        "ffmpeg", "-y",
        "-i", manifest_url,
        "-vn",
        "-acodec", "copy",
        str(tmp_path),
    ]

    print(f"  Downloading via ffmpeg...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  ERROR: ffmpeg failed:")
        print(result.stderr[-1000:])
        if tmp_path.exists():
            tmp_path.unlink()
        return False

    tmp_path.rename(output_path)
    size_mb = output_path.stat().st_size / 1_048_576
    print(f"  Saved {size_mb:.1f} MB → {output_path.relative_to(PROJECT_ROOT)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bulk-download one BBC Sounds episode per month via Genome search"
    )
    parser.add_argument(
        "--period", choices=["covid", "control"], required=True,
        help="Which period's months to download"
    )
    parser.add_argument(
        "--source", default="bbc_radio4",
        help="Source name under data/raw/ (default: bbc_radio4)"
    )
    parser.add_argument(
        "--programme", default="six o'clock news",
        help="Programme name to search for on Genome"
    )
    parser.add_argument(
        "--service", default="bbc_radio_fourfm",
        help="Genome service code (default: bbc_radio_fourfm)"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Re-download months that already have an .m4a file"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Find Sounds URLs but do not download audio"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Print Genome request URLs and raw results"
    )
    args = parser.parse_args()

    months = COVID_MONTHS if args.period == "covid" else CONTROL_MONTHS

    plan: list[tuple[int, int, str, Path]] = []  # (year, month, sounds_url, out_path) — phase 1 results

    print(f"Searching Genome for '{args.programme}' ({args.service}) ...")
    for year, month in months:
        month_name = MONTH_NAMES[month]
        out_path = (DATA_DIR / args.source / args.period
                    / str(year) / f"{month_name} {year}.m4a")

        if out_path.exists() and out_path.stat().st_size > 0 and not args.overwrite:
            print(f"  [SKIP] {month_name} {year} — already downloaded")
            continue

        print(f"  Searching {month_name} {year}...", end=" ", flush=True)
        sounds_url = find_episode_for_month(
            args.programme, args.service, year, month, debug=args.debug
        )

        if sounds_url:
            print(f"found → {sounds_url}")
            plan.append((year, month, sounds_url, out_path))
        else:
            print("NOT FOUND — skipping")

    if not plan:
        print("Nothing to download.")
        return

    if args.dry_run:
        print(f"\nDry run — would download {len(plan)} episode(s):")
        for year, month, sounds_url, out_path in plan:
            print(f"  {MONTH_NAMES[month]} {year}  {sounds_url}")
            print(f"    → {out_path.relative_to(PROJECT_ROOT)}")
        return

    print(f"\nDownloading {len(plan)} episode(s)...")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        if SESSION_FILE.exists():
            context = browser.new_context(storage_state=str(SESSION_FILE))
        else:
            context = browser.new_context()

        page = context.new_page()

        for year, month, sounds_url, out_path in plan:
            month_name = MONTH_NAMES[month]
            print(f"\n[{month_name} {year}] {sounds_url}")

            manifest = intercept_manifest(page, sounds_url)
            context.storage_state(path=str(SESSION_FILE))  # persist session

            if not manifest:
                print(f"  ERROR: no manifest found — skipping")
                continue

            download_audio(manifest, out_path)

        browser.close()

    print("\nDone.")


if __name__ == "__main__":
    main()
