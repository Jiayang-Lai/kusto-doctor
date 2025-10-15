"""Utility functions"""

from typing import List

from azure.kusto.data import KustoClient, KustoConnectionStringBuilder

from .constants import DEFAULT_KUSTO_EMULATOR_URI
from .logging import get_logger

logger = get_logger()


def buildKustoClient(
    kcsb: KustoConnectionStringBuilder = None, backend_uri: str = DEFAULT_KUSTO_EMULATOR_URI
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
