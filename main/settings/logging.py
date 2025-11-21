import logging
import os
from typing import Any

from django.conf import settings
from pythonjsonlogger.jsonlogger import JsonFormatter

# Define the path to the logs folder
# Define path: ROOT_DIR/tmp/logs
LOGS_FOLDER = os.path.join(settings.ROOT_DIR, "tmp", "logs")

# Create 'tmp' and 'logs' folders (ignore if they already exist)
os.makedirs(LOGS_FOLDER, exist_ok=True)


class FlexibleJsonFormatter(JsonFormatter):
    def add_fields(self, log_record: Any, record: Any, message_dict: Any) -> None:
        super().add_fields(log_record, record, message_dict)
        # Add default values for missing fields to ensure compatibility
        log_record.setdefault("trace_id", getattr(record, "trace_id", "no-trace-id"))
        log_record.setdefault("correlation_id", getattr(record, "correlation_id", None))
        log_record.setdefault("request", None)
        log_record.setdefault("server_time", None)
        log_record.setdefault("status_code", None)


class CustomFormatter(logging.Formatter):
    def format(self, record: Any) -> Any:
        # Add default values for missing fields to ensure compatibility
        if not hasattr(record, "trace_id"):
            record.trace_id = getattr(record, "trace_id", "no-trace-id")
        if not hasattr(record, "correlation_id"):
            record.correlation_id = getattr(record, "correlation_id", None)

        # Format the message first
        formatted_message = super(CustomFormatter, self).format(record)

        # Append extra context if available
        extras = []
        # Standard LogRecord attributes to ignore
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "message",
            "asctime",
            "trace_id",
            "correlation_id",
        }

        for key, value in record.__dict__.items():
            if key not in standard_attrs and value is not None:
                extras.append(f"{key}={value}")

        if extras:
            formatted_message = f"{formatted_message} | {' '.join(extras)}"

        return formatted_message


# Common handlers
default_handlers = ["file", "console"]

# Common loggers
base_loggers = {
    # "basehttp": {
    #     "handlers": default_handlers,
    #     "level": "INFO",
    #     "propagate": False,
    # },
    "django": {
        "handlers": default_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "django.request": {
        "handlers": default_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "django.db.backends": {
        "handlers": default_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "uvicorn.access": {
        "handlers": default_handlers,
        "level": "INFO",
        "propagate": False,
    },
    "uvicorn.error": {
        "handlers": default_handlers,
        "level": "INFO",
        "propagate": False,
    },
    # This is the root logger for everything else
    "": {
        "handlers": default_handlers,
        "level": "INFO",
        "propagate": False,
    },
}


def get_base_logging_config() -> dict:
    """
    Returns the base logging configuration
    """
    LOG_FORMAT = "{levelname} {asctime} {module} {trace_id} {correlation_id} " "{process} {thread} {message}"
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "()": CustomFormatter,
                "format": LOG_FORMAT,
                # "format": "→ {levelname:<8} | {asctime} | {module:<15} | {trace_id} | {process:5d} | {thread:5d} | {message} | {request} | {server_time} | {status_code}",
                # "format": "<{levelname:<8}> {asctime} <{module:<15}> <{trace_id}> {process:5d} {thread:5d} <{message}> {request} {server_time} <{status_code}>",
                "style": "{",
            },
            # "json": {
            #     "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            #     # Customizable format for JSON output
            #     "format": "%(levelname)s %(asctime)s %(module)s %(trace_id)s %(process)d %(thread)d %(message)s",
            # },
            "json": {
                "()": FlexibleJsonFormatter,  # Use the flexible formatter
                "format": '{"levelname": "%(levelname)s", "asctime": "%(asctime)s", "module": "%(module)s", '
                '"trace_id": "%(trace_id)s", "correlation_id": "%(correlation_id)s", "process": %(process)d, "thread": %(thread)d, '
                '"message": "%(message)s"}',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
                "filters": ["trace_id_filter"],
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "when": "midnight",
                "interval": 1,
                "filename": f"{LOGS_FOLDER}/service.log",
                "backupCount": 10,
                "formatter": "json",
                "filters": ["trace_id_filter"],
                # "formatter": "json",
            },
        },
        "filters": {
            "trace_id_filter": {
                "()": "common.middleware.TraceIDContextFilter",
            },
        },
        "loggers": base_loggers.copy(),
    }


def add_splunk_handler(log_config: dict) -> None:
    """
    Adds Splunk handler to the logging configuration
    """
    splunk_handler = {
        "class": "splunk_handler.SplunkHandler",
        "level": "INFO",
        "formatter": "json",
        "host": os.environ["splunk_host"],
        "port": int(os.environ["splunk_port"]),
        "token": os.environ["splunk_token"],
        "index": os.environ["splunk_index"],
        "verify": False,
        "flush_interval": 5,
    }

    log_config["handlers"]["splunk"] = splunk_handler
    for logger in ["", "django", "django.request", "django.db.backends", "uvicorn.access", "uvicorn.error"]:
        log_config["loggers"][logger]["handlers"] += ["splunk"]
        log_config["loggers"][logger]["level"] = "INFO"
        log_config["loggers"][logger]["propagate"] = False


def exclude_loggers(log_config: dict) -> None:
    """
    Excludes unwanted loggers in specific environments
    """
    log_config["loggers"].pop("django.server", None)
    log_config["loggers"].pop("django.template", None)


def include_loggers(log_config: dict) -> None:
    """
    Includes django.server and django.template loggers for development
    """
    log_config["loggers"]["django.server"] = {
        "handlers": ["file", "console"],
        "level": "INFO",
        "propagate": False,
    }
    log_config["loggers"]["django.template"] = {
        "handlers": ["file", "console"],
        "level": "INFO",
        "propagate": False,
    }


# Initialize logging configuration
LOGGING = get_base_logging_config()

# Customize based on APP_ENV
if settings.APP_ENV in ("qa", "dev", "prod", "staging"):
    # add_splunk_handler(LOGGING) # TODO: To enable the splunk logging
    exclude_loggers(LOGGING)
else:
    include_loggers(LOGGING)
