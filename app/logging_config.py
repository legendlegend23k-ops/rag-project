import logging
import sys
from logging.config import dictConfig


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "request_id": {"()": RequestIdFilter},
            },
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "standard",
                    "filters": ["request_id"],
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console"],
            },
        }
    )
