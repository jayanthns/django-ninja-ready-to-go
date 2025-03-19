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
        log_record.setdefault("trace_id", "00000000-0000-0000-0000-000000000000")
        log_record.setdefault("request", None)
        log_record.setdefault("server_time", None)
        log_record.setdefault("status_code", None)


class CustomFormatter(logging.Formatter):
    def format(self, record: Any) -> Any:
        # Add default values for missing fields to ensure compatibility
        if not hasattr(record, "trace_id"):
            record.trace_id = "00000000-0000-0000-0000-000000000000"
        if not hasattr(record, "request"):
            record.request = None
        if not hasattr(record, "server_time"):
            record.server_time = None
        if not hasattr(record, "status_code"):
            record.status_code = None
        return super(CustomFormatter, self).format(record)


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
    LOG_FORMAT = (
        "{levelname} {asctime} {module} {trace_id} "
        "{process} {thread} {message} {request} "
        "{server_time} {status_code}"
    )
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
                '"trace_id": "%(trace_id)s", "process": %(process)d, "thread": %(thread)d, '
                '"message": "%(message)s", "request": "%(request)s", "server_time": "%(server_time)s", '
                '"status_code": "%(status_code)s"}',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "when": "midnight",
                "interval": 1,
                "filename": f"{LOGS_FOLDER}/service.log",
                "backupCount": 10,
                "formatter": "verbose",
                # "formatter": "json",
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
