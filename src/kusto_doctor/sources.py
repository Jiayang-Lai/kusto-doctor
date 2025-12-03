"""
This module implements the Strategy pattern for loading Kusto tables
from various sources.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generator

from .exceptions import SourceLoadError
from .models import ColumnSchema, IngestionMethod, KustoDataType
from .utils import extract_nested_value


class TableSource(ABC):
    """Abstract base class for a source that can provide table data."""

    @abstractmethod
    def load(
        self,
    ) -> Generator[
        tuple[str, list[ColumnSchema], list[dict | str], IngestionMethod],
        None,
        None,
    ]:
        """Loads data from the source and returns it as a generator.

        Yields:
            A generator of tuples, each containing:
            - table_name (str)
            - schema (list of ColumnSchema)
            - table_data (list of dicts (for inline) or str (for from_storage))
            - load_type (IngestionMethod): how to ingest the data
        """


class DirectoryTableSource(TableSource):
    """Loads table data and schema from a directory with default folder structure."""

    def __init__(self, directory: Path):
        if not isinstance(directory, Path):
            raise ValueError("directory must be a pathlib.Path object")
        self.directory = directory

    def load_schema(self, schema_file: Path) -> list[ColumnSchema]:
        """Loads the schema from a JSON file."""
        if not schema_file.exists() or not schema_file.is_file():
            raise SourceLoadError(
                f"Schema file {schema_file} does not exist or is not a file."
            )

        with schema_file.open(encoding="utf8") as f:
            raw_schema = json.load(f)
            schema = [
                ColumnSchema(
                    ColumnName=col["ColumnName"],
                    ColumnType=KustoDataType(col["ColumnType"]),
                )
                for col in raw_schema
            ]

        return schema

    def load_data(self, data_file: Path) -> list[dict]:
        """Loads the table data from a JSON file."""
        if not data_file.exists() or not data_file.is_file():
            raise SourceLoadError(
                f"Data file {data_file} does not exist or is not a file."
            )

        with data_file.open(encoding="utf8") as f:
            data = json.load(f)

        return data

    def load_from_files(
        self, schema_file: Path, data_file: Path
    ) -> tuple[list[ColumnSchema], list[dict]]:
        """Loads schema and data from specified files."""
        schema = self.load_schema(schema_file)
        data = self.load_data(data_file)

        return schema, data

    def load(
        self,
    ) -> Generator[
        tuple[str, list[ColumnSchema], list[dict | str], IngestionMethod],
        None,
        None,
    ]:
        if not self.directory.exists() or not self.directory.is_dir():
            raise SourceLoadError(
                f"Directory {self.directory} does not exist or is not a directory."
            )

        try:
            for table_folder in self.directory.iterdir():
                if not table_folder.is_dir():
                    continue

                load_type = IngestionMethod.INLINE  # Default load type

                if (table_folder / "from_storage").exists():
                    # From storage ingestion
                    load_type = IngestionMethod.FROM_STORAGE
                    source_file = table_folder / "from_storage"
                    if not source_file.is_file():
                        raise SourceLoadError(
                            "Expected a file at "
                            f"{source_file} for from_storage ingestion."
                        )
                    data = self.load_data(source_file)
                    schema = self.load_schema(table_folder / "schema.json")

                    yield table_folder.name, schema, data, load_type
                    continue

                # Inline data ingestion
                schema: list[ColumnSchema] = []
                data = None
                schema_file = table_folder / "schema.json"
                data_file = table_folder / "data.json"
                schema, data = self.load_from_files(schema_file, data_file)

                yield table_folder.name, schema, data, load_type

        except Exception as e:
            raise SourceLoadError(
                f"Failed to load data from {self.directory}: {e}"
            ) from e


class QuerySource(ABC):
    """Abstract base class for a source that can provide Kusto queries."""

    @abstractmethod
    def load_queries(self) -> Generator[tuple[str, str], None, None]:
        """Loads queries from the source.

        Returns:
            A generator that returns dictionary mapping query names to query strings.
        """


class DirectoryQuerySource(QuerySource):
    """Loads Kusto queries from a directory."""

    def __init__(self, directory: Path, navigator: list[str] = None):
        if not isinstance(directory, Path):
            raise ValueError("directory must be a pathlib.Path object")
        self.directory = directory
        self.navigator = navigator or []
        if not self.directory.exists() or not self.directory.is_dir():
            raise SourceLoadError(
                f"Directory {self.directory} does not exist or is not a directory."
            )

    def load_queries(self) -> Generator[tuple[str, str], None, None]:
        if not self.directory.exists() or not self.directory.is_dir():
            raise SourceLoadError(
                f"Directory {self.directory} does not exist or is not a directory."
            )

        try:
            for file in self.directory.iterdir():
                if file.is_file() and file.suffix == ".json":
                    query_object = None
                    with file.open(encoding="utf8") as f:
                        query_object = json.load(f)
                    query_object = extract_nested_value(query_object, self.navigator)
                    yield file.stem, query_object
        except Exception as e:
            raise SourceLoadError(
                f"Failed to load queries from {self.directory}: {e}"
            ) from e
