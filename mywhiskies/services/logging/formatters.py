import json
import logging
from typing import Any, Dict


class JsonFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_object: Dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "location": f"{record.pathname}:{record.lineno}",
            "function": record.funcName,
        }

        # Add extra fields if present
        if hasattr(record, "user"):
            log_object["user"] = record.user
        if hasattr(record, "ip"):
            log_object["ip"] = record.ip
        if hasattr(record, "request_id"):
            log_object["request_id"] = record.request_id
        if hasattr(record, "duration_ms"):
            log_object["duration_ms"] = record.duration_ms

        return json.dumps(log_object)
