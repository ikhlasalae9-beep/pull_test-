from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from scrapy.crawler import CrawlerProcess
    from scrapy.utils.project import get_project_settings
except ImportError:
    print("Scrapy is not installed.")
    print("Run: python -m pip install -r requirements-scraping.txt")
    raise SystemExit(1)


HERE = Path(__file__).resolve()
SCRAPING_DIR = HERE.parent
REPO_ROOT = HERE.parents[2]
DEFAULT_OUTPUT = REPO_ROOT / "data" / "raw" / "maisonlux_scrapy_v3.csv"
DEFAULT_FAILURES = REPO_ROOT / "data" / "raw" / "maisonlux_scrapy_failures_v3.jsonl"
DEFAULT_RATE_LIMIT_STATE = REPO_ROOT / "data" / "raw" / ".mubawab-rate-limit.json"

if str(SCRAPING_DIR) not in sys.path:
    sys.path.insert(0, str(SCRAPING_DIR))

from maisondelux_scraper.rate_limit import active_cooldown  # noqa: E402
from maisondelux_scraper.spiders.mubawab import CITY_SEEDS, MubawabSpider  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Resumable Mubawab collector: public city pages, Scrapy, and "
            "RealEstateListing JSON-LD first."
        )
    )
    parser.add_argument(
        "--max-city-pages",
        type=int,
        default=len(CITY_SEEDS),
        help=f"Number of diversified public first-page city seeds (1-{len(CITY_SEEDS)}).",
    )
    parser.add_argument(
        "--max-listings",
        type=int,
        default=20,
        help="Maximum new detail pages scheduled in this run.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--failures-output", type=Path, default=DEFAULT_FAILURES)
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.max_city_pages <= len(CITY_SEEDS):
        parser.error(f"--max-city-pages must be between 1 and {len(CITY_SEEDS)}")
    if args.max_listings < 1:
        parser.error("--max-listings must be positive")

    output = args.output.resolve()
    failures_output = args.failures_output.resolve()
    rate_limit_state = DEFAULT_RATE_LIMIT_STATE.resolve()
    cooldown = active_cooldown(rate_limit_state)
    if cooldown:
        if cooldown.get("invalid"):
            print(f"Collection paused: malformed cooldown marker at {rate_limit_state}")
        else:
            print(
                "Collection paused after an earlier HTTP 429. "
                f"Resume after {cooldown['resume_after']} "
                f"({cooldown['remaining_seconds']}s remaining)."
            )
        return 75

    output.parent.mkdir(parents=True, exist_ok=True)
    failures_output.parent.mkdir(parents=True, exist_ok=True)

    settings = get_project_settings()
    settings.setmodule("maisondelux_scraper.settings")
    settings.set("OUTPUT_PATH", str(output), priority="cmdline")
    settings.set("FAILURES_OUTPUT", str(failures_output), priority="cmdline")
    settings.set("RATE_LIMIT_STATE_PATH", str(rate_limit_state), priority="cmdline")
    settings.set("LOG_LEVEL", args.log_level, priority="cmdline")
    settings.set("FEEDS", {}, priority="cmdline")

    print(f"Output checkpoint : {output}")
    print(f"Failure log       : {failures_output}")
    print(f"Public city pages : {args.max_city_pages}")
    print(f"New-detail budget : {args.max_listings}")
    print("Method            : Scrapy + RealEstateListing JSON-LD first")
    print("Resume            : automatic; existing native IDs/canonical URLs are skipped")

    process = CrawlerProcess(settings)
    crawler = process.create_crawler(MubawabSpider)
    process.crawl(
        crawler,
        max_city_pages=args.max_city_pages,
        max_listings=args.max_listings,
        output_path=str(output),
        failures_output=str(failures_output),
    )
    process.start(stop_after_crawl=True)

    stats = crawler.stats
    finish_reason = stats.get_value("finish_reason", "unknown")
    existing_rows = int(stats.get_value("checkpoint/existing_rows", 0) or 0)
    written = int(stats.get_value("checkpoint/rows_written", 0) or 0)
    jsonld_found = int(stats.get_value("jsonld/real_estate_listing_found", 0) or 0)
    jsonld_missing = int(stats.get_value("jsonld/real_estate_listing_missing", 0) or 0)
    print("\nCollection summary")
    print(f"  Finish reason  : {finish_reason}")
    print(f"  Existing rows  : {existing_rows}")
    print(f"  New rows       : {written}")
    print(f"  Total rows     : {existing_rows + written}")
    print(f"  JSON-LD found  : {jsonld_found}")
    print(f"  JSON-LD missing: {jsonld_missing}")

    if str(finish_reason).startswith("rate_limited_429"):
        print("Stopped conservatively on HTTP 429. The checkpoint is safe; wait before resuming.")
        return 75
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
