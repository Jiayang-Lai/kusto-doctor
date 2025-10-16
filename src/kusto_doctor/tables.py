"""Table management functions"""

from azure.kusto.data import KustoClient

from .logging import get_logger
from .models import ColumnSchema
from .utils import is_valid_kusto_table_name

logger = get_logger()


def create_table(
    client: KustoClient,
    database_name: str,
    table_name: str,
    schema: list[ColumnSchema],
):
    """Creates a table in the specified database with the given schema."""
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    logger.info(f"Attempting to create table {table_name}...")
    columns = ", ".join(
        [f"{col.ColumnName} : {col.ColumnType.value}" for col in schema]
    )
    create_table_cmd = f".create table {table_name} ({columns})"
    client.execute_mgmt(database_name, create_table_cmd)
    logger.info(f"Created table {table_name}!")


def check_if_table_exists(
    client: KustoClient, database_name: str, table_name: str
) -> bool:
    """Checks if a table exists in the specified database."""
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    try:
        query = f".show table {table_name} cslschema"
        response = client.execute_mgmt(database_name, query)
        return len(response.primary_results[0]) > 0
    except Exception as e:
        logger.exception(f"Error checking if table exists: {e}")
        return False


def clear_table(client: KustoClient, database_name: str, table_name: str):
    """Clears all data from the specified table."""
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    try:
        query = f".clear table {table_name} data"
        client.execute_mgmt(database_name, query)
        logger.info(f"Cleared data from table {table_name}.")
    except Exception as e:
        logger.exception(f"Error clearing table data: {e}")
