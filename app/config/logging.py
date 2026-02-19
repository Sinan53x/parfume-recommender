from __future__ import annotations

import logging
from typing import Any


SCRAPE_RUN_START = "scrape_run_start"
SCRAPE_RUN_END = "scrape_run_end"
SCRAPE_URL_FETCHED = "scrape_url_fetched"
SCRAPE_URL_FAILED = "scrape_url_failed"
SCRAPE_PARSE_FAILED = "scrape_parse_failed"


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    logger.log(level, event, extra={"event": event, **fields})
