"""
Centralized logging configuration and utilities for analyze-git-projects.

WHY THIS EXISTS:
- Centralizes all logging configuration in one place
- Prevents inconsistent logging formats across modules
- Provides structured logging for better debugging and monitoring
- Supports both development and production logging needs

RESPONSIBILITY:
- Configure logging format, levels, and handlers
- Provide utility functions for consistent logging across modules
- Support structured logging with context
- Handle log rotation and file management

BOUNDARIES:
- DOES: Configure loggers, format messages, manage log files
- DOES NOT: Implement business logic, handle log analysis, send alerts

RELATIONSHIPS:
- DEPENDS ON: Python's logging module, rich for formatting
- USED BY: All modules in analyze_git_projects package
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union, Literal
from contextlib import contextmanager

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback

from .config import LogLevel


# Type aliases for better readability
LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormatType = Literal["standard", "detailed", "json", "rich"]


class LoggingConfig:
    """
    Configuration class for logging setup.
    
    WHY THIS EXISTS:
    - Provides a single source of truth for logging configuration
    - Makes logging behavior configurable without code changes
    - Supports different environments (dev, test, prod)
    
    RESPONSIBILITY:
    - Store and validate logging configuration parameters
    - Provide sensible defaults for different environments
    
    BOUNDARIES:
    - DOES: Store configuration values, provide validation
    - DOES NOT: Configure loggers directly, handle file operations
    """
    
    def __init__(
        self,
        level: LogLevelType = "INFO",
        format_type: LogFormatType = "rich",
        log_dir: Optional[Union[str, Path]] = None,
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        enable_console: bool = True,
        enable_file: bool = True,
        enable_rich_traceback: bool = True,
    ) -> None:
        """
        Initialize logging configuration.
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            format_type: Format style for log messages
            log_dir: Directory for log files (defaults to ./logs)
            max_file_size: Maximum size for rotated log files
            backup_count: Number of backup files to keep
            enable_console: Whether to log to console
            enable_file: Whether to log to files
            enable_rich_traceback: Whether to use rich for exception formatting
        """
        self.level = level.upper() if isinstance(level, str) else level
        self.format_type = format_type
        self.log_dir = Path(log_dir) if log_dir else Path.cwd() / "logs"
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.enable_rich_traceback = enable_rich_traceback
        
        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)


class StructuredLogger:
    """
    Enhanced logger with structured logging capabilities.
    
    WHY THIS EXISTS:
    - Standard logging module lacks structured data support
    - Makes debugging easier with contextual information
    - Supports modern log aggregation tools
    
    RESPONSIBILITY:
    - Provide consistent interface for structured logging
    - Add contextual data to log messages
    - Ensure thread-safe logging operations
    
    BOUNDARIES:
    - DOES: Add structure to log messages, manage context
    - DOES NOT: Implement log storage, handle log rotation
    """
    
    def __init__(self, name: str, config: Optional[LoggingConfig] = None) -> None:
        """
        Initialize structured logger.
        
        Args:
            name: Logger name (usually module name)
            config: Logging configuration (uses default if None)
        """
        self.name = name
        self.config = config or LoggingConfig()
        self.logger = logging.getLogger(name)
        
        # Always reconfigure to ensure consistent state
        self._configure_logger()
    
    def _configure_logger(self) -> None:
        """Configure the underlying logger with handlers and formatters."""
        self.logger.setLevel(getattr(logging, self.config.level))
        
        # Only clear handlers if we're reconfiguring
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # Remove any existing handlers to prevent duplicates
        self.logger.propagate = False
        
        # Add console handler
        if self.config.enable_console:
            console_handler = self._create_console_handler()
            console_handler.setLevel(getattr(logging, self.config.level))
            self.logger.addHandler(console_handler)
        
        # Add file handler
        if self.config.enable_file:
            file_handler = self._create_file_handler()
            file_handler.setLevel(getattr(logging, self.config.level))
            self.logger.addHandler(file_handler)
    
    def _create_console_handler(self) -> logging.Handler:
        """Create appropriate console handler based on format type."""
        if self.config.format_type == "rich":
            handler = RichHandler(
                console=Console(stderr=True),
                show_time=True,
                show_path=True,
                markup=True,
                rich_tracebacks=self.config.enable_rich_traceback,
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
        else:
            handler = logging.StreamHandler(sys.stderr)
            formatter = self._get_formatter(self.config.format_type)
            handler.setFormatter(formatter)
        
        return handler
    
    def _create_file_handler(self) -> logging.Handler:
        """Create rotating file handler."""
        log_file = self.config.log_dir / f"{self.name}.log"
        # Ensure directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )
        formatter = self._get_formatter("detailed")
        handler.setFormatter(formatter)
        return handler
    
    def _get_formatter(self, format_type: str) -> logging.Formatter:
        """Get appropriate formatter for the specified format type."""
        formatters = {
            "standard": logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            "detailed": logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s"
            ),
            "json": logging.Formatter(
                '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
            ),
        }
        return formatters.get(format_type, formatters["standard"])
    
    def debug(self, msg: str, **context: Any) -> None:
        """Log debug message with optional context."""
        merged_context = self._get_merged_context(context)
        self.logger.debug(self._format_message(msg, merged_context))
    
    def info(self, msg: str, **context: Any) -> None:
        """Log info message with optional context."""
        merged_context = self._get_merged_context(context)
        self.logger.info(self._format_message(msg, merged_context))
    
    def warning(self, msg: str, **context: Any) -> None:
        """Log warning message with optional context."""
        merged_context = self._get_merged_context(context)
        self.logger.warning(self._format_message(msg, merged_context))
    
    def error(self, msg: str, **context: Any) -> None:
        """Log error message with optional context."""
        merged_context = self._get_merged_context(context)
        self.logger.error(self._format_message(msg, merged_context))
    
    def critical(self, msg: str, **context: Any) -> None:
        """Log critical message with optional context."""
        merged_context = self._get_merged_context(context)
        self.logger.critical(self._format_message(msg, merged_context))
    
    def exception(self, msg: str, **context: Any) -> None:
        """Log exception with traceback and optional context."""
        merged_context = self._get_merged_context(context)
        self.logger.exception(self._format_message(msg, merged_context))
    
    def _get_merged_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge provided context with stored context from context manager."""
        stored_context = getattr(self, "_context", {})
        return {**stored_context, **context}
    
    def _format_message(self, msg: str, context: Dict[str, Any]) -> str:
        """Format message with context data."""
        if not context:
            return msg
        
        # Convert context to string representation
        context_str = " ".join(f"{k}={v}" for k, v in context.items())
        return f"{msg} {context_str}"
    
    @contextmanager
    def context(self, **context: Any):
        """
        Context manager for temporarily adding context to logs.
        
        WHY THIS EXISTS:
        - Provides a clean way to add context to multiple log calls
        - Automatically cleans up context when exiting scope
        - Prevents context pollution between different operations
        
        Usage:
            with logger.context(request_id="123", user="alice"):
                logger.info("Processing request")
                logger.debug("Validating data")
        """
        # This is a simplified implementation - in practice, you might want
        # to use thread-local storage or contextvars for proper isolation
        original_context = getattr(self, "_context", {})
        self._context = {**original_context, **context}
        try:
            yield
        finally:
            self._context = original_context


# Global logger instance for the package
_package_logger: Optional[StructuredLogger] = None


def get_logger(name: Optional[str] = None) -> StructuredLogger:
    """
    Get a configured logger instance.
    
    WHY THIS EXISTS:
    - Provides consistent logger configuration across modules
    - Prevents duplicate configuration of loggers
    - Simplifies logger creation for module authors
    
    RESPONSIBILITY:
    - Return properly configured logger instances
    - Ensure consistent naming and configuration
    
    Args:
        name: Logger name (defaults to caller's module name)
        
    Returns:
        StructuredLogger: Configured logger instance
    """
    if name is None:
        # Get caller's module name
        import inspect
        frame = inspect.currentframe()
        try:
            caller_frame = frame.f_back if frame else None
            name = caller_frame.f_globals.get('__name__', 'unknown') if caller_frame else 'unknown'
        finally:
            del frame
    
    # Special handling for package-level logger
    if name == 'analyze_git_projects' or name.startswith('analyze_git_projects.'):
        global _package_logger
        if _package_logger is None:
            _package_logger = StructuredLogger('analyze_git_projects')
        return StructuredLogger(name, _package_logger.config)
    
    return StructuredLogger(name)


def configure_package_logging(
    level: LogLevelType = "INFO",
    format_type: LogFormatType = "rich",
    log_dir: Optional[Union[str, Path]] = None,
    **kwargs: Any
) -> None:
    """
    Configure global logging for the entire package.
    
    WHY THIS EXISTS:
    - Single entry point for configuring all package logging
    - Allows runtime configuration changes
    - Provides consistent configuration across all modules
    
    RESPONSIBILITY:
    - Configure the root package logger
    - Apply configuration to all package loggers
    
    Args:
        level: Logging level
        format_type: Format style for log messages
        log_dir: Directory for log files
        **kwargs: Additional configuration options
    """
    global _package_logger
    
    config = LoggingConfig(
        level=level,
        format_type=format_type,
        log_dir=log_dir,
        **kwargs
    )
    
    _package_logger = StructuredLogger('analyze_git_projects', config)
    
    # Configure rich traceback if enabled
    if config.enable_rich_traceback:
        install_rich_traceback(show_locals=True)


def set_log_level(level: LogLevelType) -> None:
    """
    Change the log level for all package loggers at runtime.
    
    WHY THIS EXISTS:
    - Allows dynamic log level changes without restart
    - Useful for debugging in production
    - Supports runtime configuration
    
    Args:
        level: New logging level
    """
    if _package_logger:
        _package_logger.config.level = level.upper()
        _package_logger.logger.setLevel(getattr(logging, level.upper()))
        
        # Reconfigure all handlers
        for handler in _package_logger.logger.handlers:
            handler.setLevel(getattr(logging, level.upper()))


# Convenience functions for quick logging
def log_debug(msg: str, **context: Any) -> None:
    """Quick debug logging using package logger."""
    if _package_logger:
        _package_logger.debug(msg, **context)


def log_info(msg: str, **context: Any) -> None:
    """Quick info logging using package logger."""
    if _package_logger:
        _package_logger.info(msg, **context)


def log_warning(msg: str, **context: Any) -> None:
    """Quick warning logging using package logger."""
    if _package_logger:
        _package_logger.warning(msg, **context)


def log_error(msg: str, **context: Any) -> None:
    """Quick error logging using package logger."""
    if _package_logger:
        _package_logger.error(msg, **context)


# Initialize package logging with defaults
configure_package_logging()