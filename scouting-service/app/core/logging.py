"""
Logging configuration for the scouting report microservice.
"""
import logging
import sys
from typing import Dict, Any

from pythonjsonlogger import jsonlogger

from app.core.config import settings, LogFormat


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for logs."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)
        log_record["service"] = settings.PROJECT_NAME
        log_record["environment"] = settings.ENVIRONMENT
        log_record["version"] = settings.VERSION


# Configure root logger
logger = logging.getLogger()
logger.setLevel(settings.LOG_LEVEL)

# Remove existing handlers
for handler in logger.handlers:
    logger.removeHandler(handler)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)

# Set formatter based on configuration
if settings.LOG_FORMAT == LogFormat.JSON:
    formatter = CustomJsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
else:
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Set log level for other libraries
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
