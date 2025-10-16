"""Functions that help ingest data into ADX cluster."""

import json
import logging
import os
from pathlib import Path

from azure.kusto.data import KustoClient

from .logging import get_logger
from .models import ColumnSchema, IngestionMethod
from .sources import DirectoryTableSource
from .tables import check_if_table_exists, clear_table, create_table
from .utils import buildKustoClient, is_valid_kusto_table_name

logger = get_logger()


def create_json_mapping(
    client: KustoClient,
    database_name: str,
    table_name: str,
    schema: list[ColumnSchema],
):
    """Creates a JSON mapping for the specified table based on the provided schema.
    Note: This will overwrite any existing mapping named 'JsonMapping'.
    The function is very basic and assumes
    that the JSON structure directly maps to the table schema.
    """
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    # https://sandervandevelde.wordpress.com/2023/05/17/test-kql-table-mappings-inline/
    logger.info(f"Creating JSON mapping for table {table_name}...")
    mapping_entries = ", ".join(
        [
            (
                f'{{ "column": "{col.ColumnName}", "path": "$.{col.ColumnName}", '
                f'"datatype": "{col.ColumnType.value}" }}'
            )
            for col in schema
        ]
    )
    create_mapping_cmd = (
        f'.create-or-alter table {table_name} ingestion json mapping "JsonMapping" '
        f"'[ {mapping_entries} ]'"
    )
    client.execute_mgmt(database_name, create_mapping_cmd)
    logger.info(f"Created JSON mapping for table {table_name}!")


def ingest_data_inline(
    client: KustoClient,
    database_name: str,
    table_name: str,
    data: list[dict],
    mapping_name: str = "JsonMapping",
):
    """Ingests data into the specified table. Only JSON format is supported.

    Note: This method uses inline ingestion, which is suitable for small datasets.
    For larger datasets, consider using ingestion from storage.
    """
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    logger.info(f"Attempting to ingest data into {table_name}...")
    for row in data:
        insert_cmd = (
            f".ingest inline into table {table_name} with "
            f"(format = 'json', ingestionMappingReference = '{mapping_name}') <| "
            f"{json.dumps(row)}"
        )
        client.execute(database_name, insert_cmd)
    logger.info(f"Data ingested into {table_name}!")


def ingest_csv_data_from_storage(
    client: KustoClient,
    database_name: str,
    table_name: str,
    source: str,
    ignore_first_record: bool = True,
):
    """Ingests data into the specified table from a storage source.
    The format must be CSV.

    Note: The file must be accessible by the Kusto cluster, e.g.,
    via a mounted volume or a public URL.
    If the first record is not a header, set ignore_first_record to False.
    """
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    logger.info(
        f"Attempting to ingest data into {table_name} from source {source}..."
    )
    ingest_first_line = "true" if ignore_first_record else "false"
    ingest_cmd = (
        f".ingest into table {table_name}(h'{source}') with "
        f"(format='csv', ignoreFirstRecord={ingest_first_line})"
    )
    client.execute_mgmt(database_name, ingest_cmd)
    logger.info(f"Data ingested into {table_name} from source {source}")


def ingest_json_data_from_storage(
    client: KustoClient,
    database_name: str,
    table_name: str,
    source: str,
    mapping_name: str = "JsonMapping",
):
    """Ingests data into the specified table from a storage source.
    The format must be JSON.

    Note: The file must be accessible by the Kusto cluster, e.g.,
    via a mounted volume or a public URL.
    """
    if not is_valid_kusto_table_name(table_name):
        raise ValueError(f"Invalid Kusto table name: {table_name}")

    logger.info(
        f"Attempting to ingest data into {table_name} from source {source}..."
    )
    ingest_cmd = (
        f".ingest into table {table_name}(h'{source}') with "
        f"(format='json', ingestionMappingReference = '{mapping_name}')"
    )
    client.execute_mgmt(database_name, ingest_cmd)
    logger.info(f"Data ingested into {table_name} from source {source}")


def load_tables_from_directory(
    sample_data_dir: str = None, database_name: str = None
):
    """Loads sample data from a directory into the specified database.

    The directory should have the following structure:
    sample_data_dir/
        Table1/ # A folder named after the table
            schema.json # A JSON file defining the schema
            data.json # A JSON file with an array of data rows
        Table2/
            schema.json
            data.json
        Table3/
            from_storage  # A json file containing a list of URLs or paths to CSV files
            schema.json
    """
    
    if sample_data_dir:
        logging.info(
            f"Using provided sample data directory: {sample_data_dir}"
        )
    else:
        sample_data_dir = os.path.join(os.getcwd(), "sampledata")
        logger.warning(
            f"No sample data directory provided. Using default: {sample_data_dir}"
        )
    # Set up Kusto connection
    logger.info("Setting up connection with the ADX cluster...")

    with buildKustoClient() as client:
        # Load schema and data files
        try:
            defaultDirectorySource = DirectoryTableSource(
                directory=Path(os.path.abspath(sample_data_dir))
            )
            for (
                table_folder,
                schema,
                table_data,
                load_type,
            ) in defaultDirectorySource.load():
                logger.info(f"Found table: {table_folder}")

                # Create table if it doesn't exist, else clear it
                if check_if_table_exists(client, database_name, table_folder):
                    logger.info(
                        f"Table {table_folder} already exists. Clearing data..."
                    )
                    clear_table(client, database_name, table_folder)
                else:
                    logger.info(
                        f"Table {table_folder} does not exist. Creating table..."
                    )
                    create_table(client, database_name, table_folder, schema)

                # Load data
                if load_type is IngestionMethod.INLINE:
                    # Create JSON mapping and ingest data
                    create_json_mapping(
                        client, database_name, table_folder, schema
                    )
                    ingest_data_inline(
                        client, database_name, table_folder, table_data
                    )
                elif load_type is IngestionMethod.FROM_STORAGE:
                    if table_data and isinstance(table_data, list):
                        for row in table_data:
                            if not isinstance(row, str):
                                raise ValueError(
                                    f"Expected each entry in from_storage to be a string "
                                    f"path, got {type(row)}"
                                )
                            ingest_csv_data_from_storage(
                                client, database_name, table_folder, row
                            )
                    elif table_data and isinstance(table_data, str):
                        ingest_csv_data_from_storage(
                            client, database_name, table_folder, table_data
                        )
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
            raise e
    logger.info("Done Loading sample data!")
