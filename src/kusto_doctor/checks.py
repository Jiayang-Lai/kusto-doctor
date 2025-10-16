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
    """Checks a single query for syntax and execution errors.

    Returns tuple of (a pandas DataFrame if successful, error message string if the query failed).
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
) -> dict:
    """Executes queries and produces human-readable results.

    Returns a dictionary with query name as key and query result or error message as value.


    The schema of the returned dictionary is as follows:

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
            client, query_name, query, query_properties
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
) -> dict:
    """Executes queries from a list and produces human-readable results.

    Returns a dictionary with query name as key and query result or error message as value.

    The schema of the returned dictionary is as follows:

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
            client, query_name, query, query_properties
        )
        if error:
            results["errors"][query_name] = error
        else:
            results["success"][query_name] = result

    return results
