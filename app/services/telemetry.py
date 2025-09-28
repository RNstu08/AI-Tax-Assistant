from __future__ import annotations
import logging
import sys
import structlog

def configure_logging(json_logs: bool = True, level: str = "INFO") -> None:
    """
    Configure structlog + stdlib logging.
    - json_logs=True -> JSON suitable for production/CI
    - json_logs=False -> developer-friendly console renderer
    """
    processors = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
    ]
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    structlog.configure(processors=processors)
    logging.basicConfig(stream=sys.stdout, level=getattr(logging, level.upper(), logging.INFO))