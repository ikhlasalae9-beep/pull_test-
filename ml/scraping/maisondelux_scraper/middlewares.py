"""Conservative retry/backoff and explicit HTTP 429 crawl pausing."""
from __future__ import annotations

import inspect
from pathlib import Path

from scrapy.downloadermiddlewares.retry import RetryMiddleware, get_retry_request
from scrapy.exceptions import IgnoreRequest

from .rate_limit import parse_retry_after, write_cooldown


TRANSIENT_HTTP_CODES = frozenset({408, 500, 502, 503, 504, 522, 524})
GET_RETRY_SUPPORTS_GIVE_UP_LOG_LEVEL = (
    "give_up_log_level" in inspect.signature(get_retry_request).parameters
)


def retry_backoff_seconds(attempt: int, *, base: float, maximum: float) -> float:
    return min(maximum, base * (2 ** max(0, attempt - 1)))


class ConservativeRetryMiddleware(RetryMiddleware):
    """Retry transient failures slowly; never retry an HTTP 429 in the same crawl."""

    def __init__(self, crawler):
        super().__init__(crawler.settings)
        self.crawler = crawler
        settings = crawler.settings
        self.transient_http_codes = frozenset(
            settings.getlist("RETRY_HTTP_CODES") or TRANSIENT_HTTP_CODES
        ) - {429}
        self.backoff_base = settings.getfloat("RETRY_BACKOFF_BASE", 10.0)
        self.backoff_max = settings.getfloat("RETRY_BACKOFF_MAX", 60.0)
        self.rate_limit_pause = settings.getint("RATE_LIMIT_COOLDOWN_SECONDS", 900)
        marker = settings.get("RATE_LIMIT_STATE_PATH")
        self.rate_limit_state_path = Path(marker) if marker else None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_response(self, request, response, spider=None):
        spider = spider or self.crawler.spider
        if request.meta.get("dont_retry"):
            return response

        if response.status == 429:
            retry_after_raw = response.headers.get(b"Retry-After")
            retry_after = parse_retry_after(retry_after_raw)
            pause_seconds = max(self.rate_limit_pause, retry_after or 0)
            if self.rate_limit_state_path:
                write_cooldown(
                    self.rate_limit_state_path,
                    pause_seconds=pause_seconds,
                    url=response.url,
                    retry_after_header=(
                        retry_after_raw.decode("ascii", errors="ignore")
                        if retry_after_raw
                        else None
                    ),
                )
            reason = f"rate_limited_429_pause_{pause_seconds}s"
            self.crawler.stats.inc_value("rate_limit/http_429")
            self.crawler.stats.set_value("rate_limit/pause_seconds", pause_seconds)
            spider.logger.error(
                "HTTP 429 received from %s. Stopping without retry; resume after at least %ss.",
                response.url,
                pause_seconds,
            )
            self.crawler.engine.close_spider(spider, reason=reason)
            raise IgnoreRequest(reason)

        if response.status in self.transient_http_codes:
            return self._retry_with_backoff(
                request,
                reason=f"HTTP {response.status}",
            ) or response
        return response

    def process_exception(self, request, exception, spider=None):
        if request.meta.get("dont_retry"):
            return None
        if isinstance(exception, self.exceptions_to_retry):
            return self._retry_with_backoff(request, reason=exception, spider=spider)
        return None

    def _retry_with_backoff(self, request, *, reason, spider=None):
        spider = spider or self.crawler.spider
        retry_kwargs = {
            "spider": spider,
            "reason": reason,
            "max_retry_times": request.meta.get("max_retry_times", self.max_retry_times),
            "priority_adjust": request.meta.get("priority_adjust", self.priority_adjust),
        }
        if GET_RETRY_SUPPORTS_GIVE_UP_LOG_LEVEL:
            retry_kwargs["give_up_log_level"] = request.meta.get(
                "give_up_log_level",
                getattr(self, "give_up_log_level", "ERROR"),
            )
        retry_request = get_retry_request(request, **retry_kwargs)
        if retry_request is None:
            return None
        attempt = int(retry_request.meta.get("retry_times", 1))
        delay = retry_backoff_seconds(
            attempt,
            base=self.backoff_base,
            maximum=self.backoff_max,
        )
        spider.logger.warning(
            "Transient failure for %s; retry %s/%s after %.1fs (%s)",
            request.url,
            attempt,
            self.max_retry_times,
            delay,
            reason,
        )
        from twisted.internet import reactor, task

        return task.deferLater(reactor, delay, lambda: retry_request)


__all__ = [
    "ConservativeRetryMiddleware",
    "TRANSIENT_HTTP_CODES",
    "retry_backoff_seconds",
]
