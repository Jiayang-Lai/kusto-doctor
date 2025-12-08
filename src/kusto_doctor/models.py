"""Data models for Kusto Analyzer."""

from dataclasses import dataclass
from enum import Enum


class KustoDataType(Enum):
    """Enumeration of valid Kusto data types.

    Reference: https://learn.microsoft.com/en-us/azure/data-explorer/kusto/query/scalar-data-types
    """

    bool = "bool"
    datetime = "datetime"
    decimal = "decimal"
    dynamic = "dynamic"
    guid = "guid"
    int = "int"
    long = "long"
    real = "real"
    string = "string"
    timespan = "timespan"


@dataclass
class ColumnSchema:
    """Schema definition for a Kusto table column."""

    ColumnName: str  # Name of the column
    ColumnType: KustoDataType  # Type of the column


class IngestionMethod(Enum):
    """Enumeration of ingestion methods."""

    INLINE = "inline"
    FROM_STORAGE = "from_storage"
