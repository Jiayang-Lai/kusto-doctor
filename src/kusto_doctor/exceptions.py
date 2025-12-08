"""This module contains custom exceptions for the Kusto-Analyzer package."""


class KustoAnalyzerError(Exception):
    """Base exception for all errors raised by this package."""


class NoTablesError(KustoAnalyzerError):
    """Raised when an analysis is attempted without adding any tables."""


class SourceLoadError(KustoAnalyzerError):
    """Raised when a data source fails to load."""
