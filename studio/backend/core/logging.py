import json
import logging
from datetime import datetime, timezone

from backend.core.config import settings

_logging_configured = False


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.name,
        }
        return json.dumps(payload)


def _configure_logging() -> None:
    global _logging_configured

    root_logger = logging.getLogger()
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)

    if _logging_configured:
        root_logger.setLevel(level)
        return

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root_logger.handlers = [handler]
    root_logger.setLevel(level)
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    _configure_logging()
    return logging.getLogger(name)

