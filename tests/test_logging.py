"""
Comprehensive tests for the centralized logging module.

WHY THIS EXISTS:
- Ensures logging configuration works as expected across all scenarios
- Validates structured logging functionality with type safety
- Tests different log levels, formats, and edge cases
- Provides comprehensive coverage for production reliability

RESPONSIBILITY:
- Test all public APIs of the logging module
- Validate configuration options and their interactions
- Ensure thread safety and proper resource cleanup
- Verify structured logging context handling
"""

import logging
import tempfile
import os
import sys
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Generator, Tuple, cast, Literal
from unittest.mock import Mock, patch, MagicMock

import pytest
from _pytest.logging import LogCaptureFixture

# Store temp directories created during tests for cleanup
_temp_dirs_created = []

@pytest.fixture(scope="session", autouse=True)
def cleanup_project_logs():
    """Clean up log files created in the project logs directory after all tests."""
    # Store original log directory path
    project_logs_dir = Path.cwd() / "logs"
    
    yield
    
    # After all tests complete, clean up log files in project logs directory
    if project_logs_dir.exists():
        for log_file in project_logs_dir.glob("*.log*"):
            try:
                log_file.unlink()
            except Exception:
                pass
    
    # Also clean up any log files in project root
    for log_file in Path.cwd().glob("*.log"):
        try:
            log_file.unlink()
        except Exception:
            pass

@pytest.fixture(scope="function", autouse=True)
def track_temp_dirs():
    """Track temporary directories created during tests for cleanup."""
    initial_temp_count = len(os.listdir(tempfile.gettempdir()))
    yield
    # After each test, find and clean up any new temp directories
    current_temp_dirs = [
        os.path.join(tempfile.gettempdir(), d) 
        for d in os.listdir(tempfile.gettempdir()) 
        if d.startswith('tmp')
    ]
    
    for temp_dir in current_temp_dirs:
        if os.path.isdir(temp_dir):
            # Remove all log files from temp directory
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.log') or '.log.' in file:
                        try:
                            os.remove(os.path.join(root, file))
                        except Exception:
                            pass

from analyze_git_projects.logging import (
    StructuredLogger,
    LoggingConfig,
    get_logger,
    configure_package_logging,
    set_log_level,
    log_debug,
    log_info,
    log_warning,
    log_error,
)


# Type aliases for test data
LogLevelType = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
TestLogData = Dict[str, Union[str, int, bool]]


@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    """
    Provide a temporary directory for log files.
    
    Yields:
        Path: Temporary directory path for log files
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration after each test."""
    # Reset the package logger to ensure clean state
    from analyze_git_projects.logging import _package_logger
    if _package_logger:
        # Clear handlers and reset configuration
        for handler in _package_logger.logger.handlers[:]:
            _package_logger.logger.removeHandler(handler)
        _package_logger.config = None
    _package_logger = None
    
    # Reset the root logger
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    root_logger.setLevel(logging.WARNING)

@pytest.fixture
def basic_config(temp_log_dir: Path) -> LoggingConfig:
    """
    Provide a basic logging configuration for testing.
    
    Args:
        temp_log_dir: Temporary directory fixture
        
    Returns:
        LoggingConfig: Basic test configuration
    """
    return LoggingConfig(
        level="DEBUG",
        log_dir=temp_log_dir,
        enable_console=False,
        enable_file=True,
    )


@pytest.fixture
def mock_logger() -> Generator[Mock, None, None]:
    """
    Provide a mock logger for testing logging interactions.
    
    Yields:
        Mock: Mocked logger instance
    """
    with patch('analyze_git_projects.logging.logging.getLogger') as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        yield mock_logger


class TestLoggingConfig:
    """Comprehensive tests for LoggingConfig class."""
    
    def test_default_config_values(self) -> None:
        """Test that default configuration values are correctly set."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config: LoggingConfig = LoggingConfig(log_dir=tmp_dir)
            
            assert config.level == "INFO"
            assert config.format_type == "rich"
            assert config.log_dir == Path(tmp_dir)
        assert config.max_file_size == 10 * 1024 * 1024  # 10MB
        assert config.backup_count == 5
        assert config.enable_console is True
        assert config.enable_file is True
        assert config.enable_rich_traceback is True
    
    def test_custom_config_values(self, temp_log_dir: Path) -> None:
        """Test custom configuration values are properly applied."""
        config: LoggingConfig = LoggingConfig(
            level="DEBUG",
            format_type="detailed",
            log_dir=temp_log_dir,
            max_file_size=1024,
            backup_count=3,
            enable_console=False,
            enable_file=False,
            enable_rich_traceback=False,
        )
        
        assert config.level == "DEBUG"
        assert config.format_type == "detailed"
        assert config.log_dir == temp_log_dir
        assert config.max_file_size == 1024
        assert config.backup_count == 3
        assert config.enable_console is False
        assert config.enable_file is False
        assert config.enable_rich_traceback is False
    
    def test_log_dir_creation_on_init(self, temp_log_dir: Path) -> None:
        """Test that log directory is created during initialization."""
        log_dir: Path = temp_log_dir / "new_test_logs"
        assert not log_dir.exists()
        
        config: LoggingConfig = LoggingConfig(log_dir=log_dir)
        assert log_dir.exists()
        assert log_dir.is_dir()
    
    @pytest.mark.parametrize(
        "level,expected_level",
        [
            ("debug", "DEBUG"),
            ("info", "INFO"),
            ("warning", "WARNING"),
            ("error", "ERROR"),
            ("critical", "CRITICAL"),
            ("DEBUG", "DEBUG"),
            ("INFO", "INFO"),
            ("WARNING", "WARNING"),
            ("ERROR", "ERROR"),
            ("CRITICAL", "CRITICAL"),
        ],
    )
    def test_level_normalization(self, level: str, expected_level: str) -> None:
        """Test that log levels are properly normalized."""
        config: LoggingConfig = LoggingConfig(level=level)
        assert config.level == expected_level
    
    def test_path_conversion(self) -> None:
        """Test that string paths are properly converted to Path objects."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            config: LoggingConfig = LoggingConfig(log_dir=tmp_dir)
            assert isinstance(config.log_dir, Path)
            assert config.log_dir == Path(tmp_dir)


class TestStructuredLogger:
    """Comprehensive tests for StructuredLogger class."""
    
    def test_basic_logger_creation(self) -> None:
        """Test basic logger creation with default configuration."""
        logger: StructuredLogger = StructuredLogger("test_logger")
        
        assert logger.name == "test_logger"
        assert logger.logger.name == "test_logger"
        assert logger.config is not None
        assert logger.config.level == "INFO"
    
    def test_logger_with_custom_config(self, basic_config: LoggingConfig) -> None:
        """Test logger creation with custom configuration."""
        logger: StructuredLogger = StructuredLogger("test_logger", basic_config)
        
        assert logger.name == "test_logger"
        assert logger.config == basic_config
        assert logger.logger.level == logging.DEBUG
    
    def test_logger_handlers_are_properly_configured(self, basic_config: LoggingConfig) -> None:
        """Test that handlers are properly configured based on config."""
        basic_config.enable_file = False
        basic_config.enable_console = True  # Ensure console is enabled
        logger: StructuredLogger = StructuredLogger("test_handlers", basic_config)
        
        handler_types: List[str] = [type(h).__name__ for h in logger.logger.handlers]
        
        # Should have console handler but no file handler
        assert len(handler_types) > 0, "Expected at least one handler"
        assert not any("RotatingFileHandler" in ht for ht in handler_types)
        assert any("StreamHandler" in ht or "RichHandler" in ht for ht in handler_types)
    
    def test_all_log_levels_function_correctly(self, temp_log_dir: Path) -> None:
        """Test that all log levels work correctly and messages are recorded."""
        config: LoggingConfig = LoggingConfig(
            level="DEBUG",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_levels", config)
        
        # Log messages at all levels
        test_messages: List[Tuple[str, str]] = [
            ("debug", "Debug test message"),
            ("info", "Info test message"),
            ("warning", "Warning test message"),
            ("error", "Error test message"),
            ("critical", "Critical test message"),
        ]
        
        for level, message in test_messages:
            log_method = getattr(logger, level)
            log_method(message)
        
        # Verify all messages were logged
        log_file: Path = temp_log_dir / "test_levels.log"
        assert log_file.exists()
        
        content: str = log_file.read_text()
        for _, message in test_messages:
            assert message in content
    
    def test_structured_logging_with_context(self, temp_log_dir: Path) -> None:
        """Test structured logging with additional context data."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_structured", config)
        
        context_data: Dict[str, Union[str, int]] = {
            "request_id": "req-12345",
            "user_id": 42,
            "operation": "data_processing",
        }
        
        logger.info("Processing user request", **context_data)
        
        log_file: Path = temp_log_dir / "test_structured.log"
        content: str = log_file.read_text()
        
        assert "Processing user request" in content
        assert "request_id=req-12345" in content
        assert "user_id=42" in content
        assert "operation=data_processing" in content
    
    def test_exception_logging_includes_traceback(self, temp_log_dir: Path) -> None:
        """Test that exception logging includes full traceback."""
        config: LoggingConfig = LoggingConfig(
            level="ERROR",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_exception", config)
        
        try:
            raise ValueError("Test exception for logging")
        except ValueError:
            logger.exception("An error occurred during processing", operation="test_operation")
        
        log_file: Path = temp_log_dir / "test_exception.log"
        content: str = log_file.read_text()
        
        assert "An error occurred during processing" in content
        assert "operation=test_operation" in content
        assert "Traceback" in content
        assert "ValueError: Test exception for logging" in content
    
    def test_context_manager_adds_temporal_context(self, temp_log_dir: Path) -> None:
        """Test context manager for adding temporary logging context."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_context", config)
        
        with logger.context(request_id="ctx-123", session="test-session"):
            logger.info("Processing within context")
        
        logger.info("Processing outside context")
        
        log_file: Path = temp_log_dir / "test_context.log"
        content: str = log_file.read_text()
        
        assert "Processing within context" in content
        assert "request_id=ctx-123" in content
        assert "session=test-session" in content
    
    def test_logger_thread_safety(self, temp_log_dir: Path) -> None:
        """Test that logger operations are thread-safe."""
        import threading
        import time
        
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_thread_safe", config)
        
        results: List[bool] = []
        
        def log_messages(thread_id: int) -> None:
            """Log messages from a specific thread."""
            try:
                for i in range(10):
                    logger.info(f"Message from thread {thread_id}", iteration=i)
                    time.sleep(0.001)  # Small delay to increase chance of race conditions
                results.append(True)
            except Exception:
                results.append(False)
        
        threads: List[threading.Thread] = []
        for thread_id in range(5):
            thread = threading.Thread(target=log_messages, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        assert all(results), "All threads should complete successfully"
        
        log_file: Path = temp_log_dir / "test_thread_safe.log"
        content: str = log_file.read_text()
        
        # Should have 50 messages (5 threads * 10 messages each)
        message_count: int = content.count("Message from thread")
        assert message_count == 50
    
    @pytest.mark.parametrize(
        "format_type,expected_type",
        [
            ("standard", "StreamHandler"),
            ("detailed", "StreamHandler"),
            ("json", "StreamHandler"),
            ("rich", "RichHandler"),
        ],
    )
    def test_format_type_configuration(
        self, format_type: str, expected_type: str, basic_config: LoggingConfig
    ) -> None:
        """Test that different format types are properly configured."""
        basic_config.format_type = format_type
        basic_config.enable_file = False  # Focus on console handler
        basic_config.enable_console = True  # Ensure console is enabled
        
        logger: StructuredLogger = StructuredLogger("test_format", basic_config)
        
        handler_types: List[str] = [type(h).__name__ for h in logger.logger.handlers]
        assert any(expected_type in ht for ht in handler_types), f"Expected {expected_type} in {handler_types}"

class TestGetLogger:
    """Comprehensive tests for get_logger function."""
    
    def test_get_logger_with_default_name(self) -> None:
        """Test getting logger with automatically determined name."""
        logger: StructuredLogger = get_logger()
        
        # Should get the test module name
        assert logger.name == "tests.test_logging"
        assert isinstance(logger, StructuredLogger)
    
    def test_get_logger_with_custom_name(self) -> None:
        """Test getting logger with explicitly provided name."""
        logger: StructuredLogger = get_logger("my_custom_logger")
        
        assert logger.name == "my_custom_logger"
        assert isinstance(logger, StructuredLogger)
    
    def test_get_logger_consistency_for_same_name(self) -> None:
        """Test that same name returns equivalent configuration."""
        logger1: StructuredLogger = get_logger("test_consistency")
        logger2: StructuredLogger = get_logger("test_consistency")
        
        assert logger1.name == logger2.name
        assert logger1.config.level == logger2.config.level
        assert logger1.config.format_type == logger2.config.format_type
    
    def test_package_logger_special_handling(self) -> None:
        """Test special handling for package-level loggers."""
        package_logger: StructuredLogger = get_logger("analyze_git_projects")
        
        assert package_logger.name == "analyze_git_projects"
        assert package_logger.config is not None
    
    def test_subpackage_logger_inheritance(self) -> None:
        """Test that subpackage loggers inherit package configuration."""
        subpackage_logger: StructuredLogger = get_logger("analyze_git_projects.submodule")
        
        assert subpackage_logger.name == "analyze_git_projects.submodule"
        assert subpackage_logger.config is not None

class TestPackageLogging:
    """Comprehensive tests for package-level logging functions."""
    
    @pytest.fixture(autouse=True)
    def reset_package_logging(self):
        """Ensure package logging is reset before each test in this class."""
        from analyze_git_projects.logging import _package_logger
        _package_logger = None
        
    
    def test_configure_package_logging_creates_global_config(self, temp_log_dir: Path) -> None:
        """Test that package logging configuration creates global logger."""
        configure_package_logging(
            level="DEBUG",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        
        # Test that logging works
        log_info("Test package configuration")
        
        log_file: Path = temp_log_dir / "analyze_git_projects.log"
        assert log_file.exists()
        
        content: str = log_file.read_text()
        assert "Test package configuration" in content
    
    def test_set_log_level_changes_runtime_behavior(self, temp_log_dir: Path) -> None:
        """Test that log level can be changed at runtime."""
        configure_package_logging(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        
        # Initially INFO level - DEBUG should not appear
        log_debug("This debug message should not appear")
        log_info("This info message should appear")
        
        log_file: Path = temp_log_dir / "analyze_git_projects.log"
        content: str = log_file.read_text()
        assert "This debug message should not appear" not in content
        assert "This info message should appear" in content
        
        # Change to DEBUG level
        set_log_level("DEBUG")
        
        # Clear the log file
        log_file.write_text("")
        
        # Now DEBUG should appear
        log_debug("This debug message should now appear")
        
        content = log_file.read_text()
        assert "This debug message should now appear" in content
        
    
    def test_convenience_functions_work_correctly(self, temp_log_dir: Path) -> None:
        """Test that convenience logging functions work as expected."""
        configure_package_logging(
            level="DEBUG",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        
        # Test all convenience functions
        log_debug("Debug convenience message", context="test")
        log_info("Info convenience message", user_id=123)
        log_warning("Warning convenience message", count=5)
        log_error("Error convenience message", error_code="E001")
        
        log_file: Path = temp_log_dir / "analyze_git_projects.log"
        content: str = log_file.read_text()
        
        assert "Debug convenience message" in content
        assert "Info convenience message" in content
        assert "Warning convenience message" in content
        assert "Error convenience message" in content
        
        # Check context is included
        assert "context=test" in content
        assert "user_id=123" in content
        assert "count=5" in content
        assert "error_code=E001" in content
    
    def test_configure_package_logging_with_kwargs(self, temp_log_dir: Path) -> None:
        """Test package configuration with additional kwargs."""
        configure_package_logging(
            level="WARNING",
            log_dir=temp_log_dir,
            max_file_size=1024,
            backup_count=2,
            enable_console=False,
            enable_file=True,
        )
        
        log_warning("Testing with custom configuration")
        
        log_file: Path = temp_log_dir / "analyze_git_projects.log"
        assert log_file.exists()
        
        content: str = log_file.read_text()
        assert "Testing with custom configuration" in content


class TestLoggingEdgeCases:
    """Tests for edge cases and error conditions."""
    
    def test_empty_context_in_structured_logging(self, temp_log_dir: Path) -> None:
        """Test structured logging with empty context."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_empty_context", config)
        
        logger.info("Message with no context")
        
        log_file: Path = temp_log_dir / "test_empty_context.log"
        content: str = log_file.read_text()
        
        assert "Message with no context" in content
    
    def test_none_values_in_context(self, temp_log_dir: Path) -> None:
        """Test handling of None values in structured logging context."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_none_context", config)
        
        logger.info("Testing None values", nullable=None, valid="value")
        
        log_file: Path = temp_log_dir / "test_none_context.log"
        content: str = log_file.read_text()
        
        assert "Testing None values" in content
        assert "valid=value" in content
    
    def test_special_characters_in_messages(self, temp_log_dir: Path) -> None:
        """Test handling of special characters in log messages."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_special_chars", config)
        
        special_messages: List[str] = [
            "Message with 'quotes' and \"double quotes\"",
            "Message with \n newlines \t and tabs",
            "Message with unicode: 你好世界 🌍",
            "Message with backslashes: C:\\Users\\test\\file.txt",
            "Message with | pipes and : colons",
        ]
        
        for message in special_messages:
            logger.info(message, category="special_chars")
        
        log_file: Path = temp_log_dir / "test_special_chars.log"
        content: str = log_file.read_text()
        
        for message in special_messages:
            assert message in content
    
    def test_very_long_messages(self, temp_log_dir: Path) -> None:
        """Test handling of very long log messages."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_long_messages", config)
        
        # Create a very long message
        long_message: str = "A" * 10000
        logger.info(long_message, length=len(long_message))
        
        log_file: Path = temp_log_dir / "test_long_messages.log"
        content: str = log_file.read_text()
        
        assert long_message in content
        assert "length=10000" in content
    
    def test_large_number_of_context_fields(self, temp_log_dir: Path) -> None:
        """Test handling of many context fields."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_many_fields", config)
        
        # Create many context fields
        context: Dict[str, Union[str, int]] = {
            f"field_{i}": f"value_{i}" if i % 2 == 0 else i
            for i in range(100)
        }
        
        logger.info("Message with many context fields", **context)
        
        log_file: Path = temp_log_dir / "test_many_fields.log"
        content: str = log_file.read_text()
        
        assert "Message with many context fields" in content
        assert "field_0=value_0" in content
        assert "field_1=1" in content
        assert "field_99=99" in content


class TestLoggingPerformance:
    """Performance and stress tests for logging."""
    
    def test_high_frequency_logging(self, temp_log_dir: Path) -> None:
        """Test logging performance under high frequency."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_performance", config)
        
        # Log many messages quickly
        num_messages: int = 1000
        for i in range(num_messages):
            logger.info(f"Performance test message {i}", batch_id="perf_test")
        
        log_file: Path = temp_log_dir / "test_performance.log"
        content: str = log_file.read_text()
        
        # Verify all messages were logged
        assert content.count("Performance test message") == num_messages
    
    def test_log_rotation_behavior(self, temp_log_dir: Path) -> None:
        """Test that log rotation works correctly."""
        config: LoggingConfig = LoggingConfig(
            level="INFO",
            log_dir=temp_log_dir,
            max_file_size=1024,  # Very small for testing
            backup_count=3,
            enable_console=False,
            enable_file=True,
        )
        logger: StructuredLogger = StructuredLogger("test_rotation", config)
        
        # Generate enough content to trigger rotation
        large_message: str = "X" * 500
        for i in range(10):
            logger.info(large_message, iteration=i)
        
        # Check that rotation occurred
        log_files: List[Path] = list(temp_log_dir.glob("test_rotation.log*"))
        assert len(log_files) >= 2  # Original + at least one backup
        
        # Verify backup files exist
        backup_files: List[Path] = list(temp_log_dir.glob("test_rotation.log.*"))
        assert len(backup_files) <= 3  # Should not exceed backup_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])