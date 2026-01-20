"""
Centralized logging configuration for the RAG Chatbot application
Provides structured logging with different levels and formatters for various components
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in a structured JSON format
    """
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'duration'):
            log_entry['duration_ms'] = record.duration
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code

        return json.dumps(log_entry)


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    use_json: bool = True
) -> logging.Logger:
    """
    Set up centralized logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for logging
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        use_json: Whether to use JSON formatting

    Returns:
        Root logger instance
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    if use_json:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        # Ensure log directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Also set specific loggers to the same level
    for logger_name in ['uvicorn', 'uvicorn.error', 'uvicorn.access']:
        logging.getLogger(logger_name).setLevel(numeric_level)

    return root_logger


def get_logger(name: str, user_id: Optional[str] = None) -> logging.LoggerAdapter:
    """
    Get a logger with optional user context

    Args:
        name: Name of the logger
        user_id: Optional user ID to include in log entries

    Returns:
        Logger adapter with optional context
    """
    logger = logging.getLogger(name)
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    return logging.LoggerAdapter(logger, extra)


def log_api_request(
    logger: logging.LoggerAdapter,
    endpoint: str,
    method: str,
    user_id: str,
    request_id: str,
    duration: float,
    status_code: int,
    message: str = "API request completed"
):
    """
    Log API request with structured data

    Args:
        logger: Logger instance
        endpoint: API endpoint
        method: HTTP method
        user_id: User ID
        request_id: Request ID
        duration: Request duration in seconds
        status_code: HTTP status code
        message: Log message
    """
    extra = {
        'endpoint': f"{method} {endpoint}",
        'user_id': user_id,
        'request_id': request_id,
        'duration': round(duration * 1000, 2),  # Convert to milliseconds
        'status_code': status_code
    }
    adapter = logging.LoggerAdapter(logger.logger, extra)
    adapter.info(message)


def log_performance_metric(
    logger: logging.LoggerAdapter,
    metric_name: str,
    value: float,
    unit: str = "",
    tags: Optional[dict] = None
):
    """
    Log performance metrics

    Args:
        logger: Logger instance
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        tags: Optional tags for the metric
    """
    extra = {
        'metric_name': metric_name,
        'metric_value': value,
        'metric_unit': unit,
        'metric_tags': tags or {}
    }
    adapter = logging.LoggerAdapter(logger.logger, extra)
    adapter.info("Performance metric recorded")


def log_security_event(
    logger: logging.LoggerAdapter,
    event_type: str,
    user_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None
):
    """
    Log security-related events

    Args:
        logger: Logger instance
        event_type: Type of security event
        user_id: User ID involved (if any)
        ip_address: IP address (if any)
        details: Additional event details
    """
    extra = {
        'event_type': event_type,
        'user_id': user_id,
        'ip_address': ip_address,
        'event_details': details or {}
    }
    adapter = logging.LoggerAdapter(logger.logger, extra)
    adapter.warning(f"Security event: {event_type}")


# Default logger setup
default_logger = None


def init_default_logger():
    """
    Initialize the default logger with standard configuration
    """
    global default_logger
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    log_level = os.getenv('LOG_LEVEL', 'INFO')

    try:
        default_logger = setup_logging(
            log_level=log_level,
            log_file=log_file,
            use_json=os.getenv('LOG_FORMAT', 'json').lower() == 'json'
        )
    except Exception as e:
        # Fallback to console-only logging if file setup fails
        default_logger = setup_logging(log_level=log_level, log_file=None)
        default_logger.warning(f"Failed to set up file logging: {e}")

    return default_logger


# Initialize default logger on import
if default_logger is None:
    init_default_logger()


# Convenience functions
def get_default_logger() -> logging.Logger:
    """
    Get the default configured logger
    """
    global default_logger
    if default_logger is None:
        default_logger = init_default_logger()
    return default_logger


def log_info(message: str, **kwargs):
    """Log an info message with optional structured data"""
    logger = get_default_logger()
    if kwargs:
        adapter = logging.LoggerAdapter(logger, kwargs)
        adapter.info(message)
    else:
        logger.info(message)


def log_error(message: str, **kwargs):
    """Log an error message with optional structured data"""
    logger = get_default_logger()
    if kwargs:
        adapter = logging.LoggerAdapter(logger, kwargs)
        adapter.error(message)
    else:
        logger.error(message)


def log_warning(message: str, **kwargs):
    """Log a warning message with optional structured data"""
    logger = get_default_logger()
    if kwargs:
        adapter = logging.LoggerAdapter(logger, kwargs)
        adapter.warning(message)
    else:
        logger.warning(message)


def log_debug(message: str, **kwargs):
    """Log a debug message with optional structured data"""
    logger = get_default_logger()
    if kwargs:
        adapter = logging.LoggerAdapter(logger, kwargs)
        adapter.debug(message)
    else:
        logger.debug(message)