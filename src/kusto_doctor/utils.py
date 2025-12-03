"""Utility functions"""

import re
from typing import List

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
from azure.kusto.ingest import KustoStreamingIngestClient

from .constants import DEFAULT_KUSTO_EMULATOR_URI
from .logging import get_logger

logger = get_logger()


def buildKustoClient(
    kcsb: KustoConnectionStringBuilder = None,
    backend_uri: str = DEFAULT_KUSTO_EMULATOR_URI,
) -> KustoClient:
    """Builds and returns a KustoClient using the provided connection string builder
    or a default one.
    """

    if kcsb is None:
        logger.info("Building Kusto client with default connection string.")
        kcsb = KustoConnectionStringBuilder.with_aad_application_token_authentication(
            connection_string=backend_uri, application_token="justafiller"
        )
    return KustoClient(kcsb)


def buildKustoStreamingIngestClient(
    kcsb: KustoConnectionStringBuilder = None,
    backend_uri: str = DEFAULT_KUSTO_EMULATOR_URI,
) -> KustoStreamingIngestClient:
    """Builds and returns a KustoStreamingIngestClient using environment variables.

    Returns:
        KustoStreamingIngestClient: Configured streaming ingest client
        for data ingestion
    """
    if kcsb is None:
        logger.info(
            "Building Kusto streaming ingest client with default connection string."
        )
        kcsb = KustoConnectionStringBuilder.with_aad_application_token_authentication(
            connection_string=backend_uri, application_token="justafiller"
        )

    return KustoStreamingIngestClient(kcsb)


def extract_nested_value(obj: dict, keys: List[str]) -> str | None:
    """Extracts a nested value from a dictionary using a list of keys.

    Args:
        obj: The dictionary to extract the value from.
        keys: A list of keys to navigate the dictionary structure.

    Returns:
        The extracted value, or None if any key is not found.
    """

    try:
        for key in keys:
            obj = obj[key]
    except KeyError:
        logger.warning(f"Keys {keys} not found in object.")
        return None
    return obj


def is_valid_kusto_table_name(table_name: str) -> bool:
    """Validates if a table name conforms to Kusto entity naming rules.

    This function helps prevent KQL injection by ensuring table names follow
    the official Microsoft Kusto naming conventions.

    Currently there is no library that provides the secure interaction with Kusto
    for validating table names, so this function implements basic checks.

    According to Microsoft documentation, valid identifiers must:
    - Be between 1 and 1024 characters long
    - Contain only letters, digits and underscores (_)
    - Use UTF-8 encoding
    - Be case-sensitive

    However, different from the reference documentation,
    **space character, dash or dot are not allowed in table names.**

    Args:
        table_name: The table name to validate

    Returns:
        bool: True if the table name is valid, False otherwise

    References:
        https://learn.microsoft.com/en-us/kusto/query/schema-entities/entity-names
    """
    if not table_name:
        return False

    # Check length constraints (1-1024 characters)
    if len(table_name) < 1 or len(table_name) > 1024:
        return False

    # Check for valid characters: letters, digits, underscores
    # Using regex pattern that matches the Kusto specification
    # (no spaces, dashes or dots allowed)
    valid_pattern = re.compile(r"^[a-zA-Z0-9_]+$")
    if not valid_pattern.match(table_name):
        return False

    # Additional security check: reject names that are reserved patterns
    # Kusto reserves identifiers starting/ending with double underscores
    if table_name.startswith("__") or table_name.endswith("__"):
        return False

    # Check for common KQL keywords that should be avoided (case-insensitive)
    # This is a basic list of common KQL keywords for injection prevention
    kql_keywords = {
        "where",
        "project",
        "extend",
        "summarize",
        "count",
        "distinct",
        "join",
        "union",
        "sort",
        "top",
        "limit",
        "take",
        "skip",
        "order",
        "by",
        "asc",
        "desc",
        "let",
        "print",
        "evaluate",
        "invoke",
        "search",
        "find",
        "make",
        "series",
        "mv-expand",
        "parse",
        "split",
        "extract",
        "replace",
        "trim",
        "tolower",
        "toupper",
        "substring",
        "strcat",
        "strlen",
        "datetime",
        "now",
        "ago",
        "bin",
        "range",
        "toscalar",
        "tostring",
        "toint",
        "tolong",
        "todouble",
        "tobool",
        "todatetime",
        "totimespan",
        "isempty",
        "isnull",
        "isnotempty",
        "isnotnull",
        "case",
        "iff",
        "iif",
        "coalesce",
        "null",
        "true",
        "false",
    }

    # Check if the table name matches any KQL keyword (case-insensitive)
    if table_name.lower() in kql_keywords:
        logger.warning(
            f"Table name '{table_name}' matches a KQL keyword and should be avoided"
        )
        return False

    return True
