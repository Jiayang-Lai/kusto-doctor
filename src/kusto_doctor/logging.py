"""Module for configuring and managing logging in the kusto_doctor package."""

import logging
import sys


class SingletonLogger:
    """Singleton logger class to ensure only one logger instance exists."""

    _instance = None
    _logger = None

    def __new__(cls):
        """Return the singleton instance of the logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_logger(
        self,
        name: str = "kusto_doctor",
        level: str = "INFO",
        console_output: bool = False,
    ) -> logging.Logger:
        """Get or creates the singleton logger instance.

        Args:
            name: Logger name (typically __name__ or module name)
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            console_output: Whether to output logs to console

        Returns:
            Configured logger instance
        """
        if self._logger is None:
            self._logger = self._setup_logger(name, level, console_output)
        return self._logger

    def _setup_logger(
        self, name: str, level: str, console_output: bool
    ) -> logging.Logger:
        """Set up the logger with the specified configuration.

        Args:
            name: Logger name
            level: Logging level
            console_output: Whether to output logs to console
        """
        # Create logger
        logger = logging.getLogger(name)

        # Prevent duplicate handlers if logger already exists
        if logger.handlers:
            logger.handlers.clear()

        # Set logging level
        logger.setLevel(getattr(logging, level.upper()))

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        else:
            # Add a null handler to prevent fallback to last resort handler
            # Keep propagation enabled so users can capture logs via root logger
            null_handler = logging.NullHandler()
            logger.addHandler(null_handler)

        return logger

    def reconfigure(
        self,
        name: str = "kusto_doctor",
        level: str = "INFO",
        console_output: bool = False,
    ):
        """Reconfigure the singleton logger with new settings."""
        self._logger = None
        self._logger = self._setup_logger(name, level, console_output)


# Public API functions for users
def configure_logging(
    level: str = "INFO",
    console_output: bool = True,
    name: str = "kusto_doctor",
) -> None:
    """Configure logging for the kusto_doctor package.

    This is the main function users should call to set up logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output logs to console (default: True)
        name: Logger name (default: "kusto_doctor")

    Example:
        >>> import kusto_doctor
        >>> kusto_doctor.configure_logging(level="DEBUG", console_output=True)
    """
    singleton = SingletonLogger()
    singleton.reconfigure(name, level, console_output)


def get_logger(
    name: str = "kusto_doctor",
    level: str = "INFO",
    console_output: bool = False,
) -> logging.Logger:
    """Get the singleton logger instance.

    Args:
        name: Logger name (typically __name__ or module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output logs to console

    Returns:
        Configured logger instance
    """
    singleton = SingletonLogger()
    return singleton.get_logger(name, level, console_output)


def disable_logging() -> None:
    """Disable all logging for the kusto_doctor package."""
    logger = logging.getLogger("kusto_doctor")
    logger.setLevel(logging.CRITICAL + 1)  # Disable all logging

    # Clear existing handlers and add null handler
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    # Note: We don't set propagate = False here to allow root logger capture


def enable_debug_logging() -> None:
    """Enable debug logging with console output."""
    configure_logging(level="DEBUG", console_output=True)
