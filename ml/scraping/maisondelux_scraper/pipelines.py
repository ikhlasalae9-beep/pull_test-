"""Scrapy item pipeline backed by the append-only CSV checkpoint store."""
from __future__ import annotations

from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem, NotConfigured

from .persistence import CheckpointCsvStore


class CheckpointCsvPipeline:
    def __init__(self, output_path: str, crawler):
        self.store = CheckpointCsvStore(Path(output_path))
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        output_path = crawler.settings.get("OUTPUT_PATH")
        if not output_path:
            raise NotConfigured("OUTPUT_PATH is required for checkpoint persistence")
        return cls(output_path, crawler)

    def open_spider(self, spider=None) -> None:
        spider = spider or self.crawler.spider
        self.store.open()
        spider.crawler.stats.set_value("checkpoint/existing_rows", self.store.existing_rows)
        spider.logger.info(
            "Checkpoint opened: %s existing rows in %s",
            self.store.existing_rows,
            self.store.path,
        )

    def process_item(self, item, spider=None):
        spider = spider or self.crawler.spider
        record = ItemAdapter(item).asdict()
        if not self.store.append(record):
            spider.crawler.stats.inc_value("checkpoint/duplicates_dropped")
            raise DropItem(f"Duplicate listing: {record.get('listing_id') or record.get('url')}")
        spider.crawler.stats.inc_value("checkpoint/rows_written")
        return item

    def close_spider(self, spider=None) -> None:
        self.store.close()


__all__ = ["CheckpointCsvPipeline"]
