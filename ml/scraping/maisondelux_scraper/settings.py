BOT_NAME = "maisondelux_scraper"

SPIDER_MODULES = ["maisondelux_scraper.spiders"]
NEWSPIDER_MODULE = "maisondelux_scraper.spiders"

# Site policy is a hard boundary for this collector.
ROBOTSTXT_OBEY = True

# Deliberately one request at a time. The randomized delay is roughly 3–9s,
# and AutoThrottle may slow it further when the site responds slowly.
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 6.0
RANDOMIZE_DOWNLOAD_DELAY = True
DOWNLOAD_TIMEOUT = 45

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 6.0
AUTOTHROTTLE_MAX_DELAY = 60.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
AUTOTHROTTLE_DEBUG = False

# 429 is intentionally absent. Our middleware persists a cooldown and stops the
# crawl instead of retrying it. Other transient failures use exponential delay.
RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408]
RETRY_BACKOFF_BASE = 10.0
RETRY_BACKOFF_MAX = 60.0
RATE_LIMIT_COOLDOWN_SECONDS = 900

DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.retry.RetryMiddleware": None,
    "maisondelux_scraper.middlewares.ConservativeRetryMiddleware": 550,
}
ITEM_PIPELINES = {
    "maisondelux_scraper.pipelines.CheckpointCsvPipeline": 300,
}

COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

USER_AGENT = (
    "MaisonDeLUXResearchCollector/1.0 "
    "(public real-estate research; respects robots.txt and rate limits)"
)
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.6",
}

FEED_EXPORT_ENCODING = "utf-8-sig"
LOG_LEVEL = "INFO"
LOGSTATS_INTERVAL = 30.0
