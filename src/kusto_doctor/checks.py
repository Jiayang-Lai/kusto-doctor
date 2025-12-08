"""Module for checking Kusto queries."""

from typing import Optional

import pandas
from azure.kusto.data import ClientRequestProperties, KustoClient
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.data.helpers import dataframe_from_result_table

from .constants import DEFAULT_DATABASE_NAME
from .logging import get_logger
from .queries import extract_queries_from_directory, extract_queries_from_list

logger = get_logger()


def check_single_query(
    client: KustoClient,
    query_name: str,
    query: str,
    query_properties: ClientRequestProperties,
    database_name: str = DEFAULT_DATABASE_NAME,
) -> tuple[Optional[pandas.DataFrame], Optional[str]]:
    """Check a single query for syntax and execution errors.

    Returns tuple of (a pandas DataFrame if successful,
    error message string if the query failed).

    Args:
        client: KustoClient instance to execute the query.
        query_name: Name of the query for logging purposes.
        query: The Kusto query to execute.
        query_properties: ClientRequestProperties for the query.
        database_name: Name of the Kusto database to run the query against.

    Returns:
        A tuple containing a pandas DataFrame with the query results if successful,
        or an error message string if the query failed.
        If the query fails, the DataFrame will be None
        and the error message will contain the error details.
    """
    try:
        response = client.execute(database_name, query, query_properties)
        logger.info(f"Query {query_name} ran successfully.")
        df = None
        if len(response.primary_results[0]) > 0:
            df = dataframe_from_result_table(response.primary_results[0])
        return df, None
    except KustoServiceError as e:
        error_msg = str(e)
        logger.error(f"Query {query_name} failed: {error_msg}")
        return None, error_msg


def check_directory_queries(
    client: KustoClient,
    detection_dir: str = None,
    query_properties: ClientRequestProperties = None,
    database_name: str = DEFAULT_DATABASE_NAME,
) -> dict:
    """Execute queries and produce human-readable results.

    Return a dictionary with query name as key
    and query result or error message as value.

    Args:
        client: KustoClient instance to execute the queries.
        detection_dir: Directory containing Kusto query files.
        query_properties: ClientRequestProperties for the queries.
        database_name: Name of the Kusto database to run the queries against.

    Returns:
        A dictionary with the following structure:

    ```
    {
        "success": {
            "query_name_1": <pandas DataFrame>,
            "query_name_2": <pandas DataFrame>,
            ...
        },
        "errors": {
            "query_name_3": "Error message string",
            "query_name_4": "Error message string",
            ...
        }
    }
    ```
    """
    queries = extract_queries_from_directory(detection_dir)
    results = {
        "success": {},
        "errors": {},
    }

    for query_name, query in queries:
        result, error = check_single_query(
            client, query_name, query, query_properties, database_name
        )
        if error:
            results["errors"][query_name] = error
        else:
            results["success"][query_name] = result

    return results


def check_list_queries(
    client: KustoClient,
    detection_list: list[tuple[str, str]],
    query_properties: ClientRequestProperties = None,
    database_name: str = DEFAULT_DATABASE_NAME,
) -> dict:
    """Execute queries from a list and produce human-readable results.

    Returns a dictionary with query name as key
    and query result or error message as value.

    Args:
        client: KustoClient instance to execute the queries.
        detection_list: List of tuples containing query names and query text.
        query_properties: ClientRequestProperties for the queries.
        database_name: Name of the Kusto database to run the queries against.

    Returns:
        A dictionary with the following structure:

    ```
    {
        "success": {
            "query_name_1": <pandas DataFrame>,
            "query_name_2": <pandas DataFrame>,
            ...
        },
        "errors": {
            "query_name_3": "Error message string",
            "query_name_4": "Error message string",
            ...
        }
    }
    ```
    """
    queries = extract_queries_from_list(detection_list)
    results = {
        "success": {},
        "errors": {},
    }

    for query_name, query in queries:
        result, error = check_single_query(
            client,
            query_name,
            query,
            query_properties,
            database_name,
        )
        if error:
            results["errors"][query_name] = error
        else:
            results["success"][query_name] = result

    return results
