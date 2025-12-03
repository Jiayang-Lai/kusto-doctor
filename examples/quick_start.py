"""
Quick Start Example for Kusto-Doctor

This example demonstrates the basic usage of Kusto-Doctor:
1. Creating a table with a custom schema
2. Ingesting sample data
3. Validating queries against the table
4. Cleaning up by clearing the table data
"""

import logging
from datetime import datetime

from azure.kusto.data import ClientRequestProperties

from kusto_doctor.checks import check_list_queries
from kusto_doctor.ingestions import create_json_mapping, ingest_data_inline
from kusto_doctor.models import ColumnSchema, KustoDataType
from kusto_doctor.tables import create_table
from kusto_doctor.utils import buildKustoClient

logging.basicConfig(level=logging.INFO)


def main():
    """Run the quick start example."""

    with buildKustoClient() as client:
        # Step 1: Create a table with custom schema
        logging.info("Creating a test table...")
        schema = [
            ColumnSchema(ColumnName="Name", ColumnType=KustoDataType.string),
            ColumnSchema(ColumnName="Age", ColumnType=KustoDataType.int),
            ColumnSchema(ColumnName="Email", ColumnType=KustoDataType.string),
            ColumnSchema(ColumnName="JoinDate", ColumnType=KustoDataType.datetime),
        ]

        create_table(
            client=client,
            database_name="NetDefaultDB",
            table_name="Users",
            schema=schema,
        )
        logging.info("Table 'Users' created successfully!")

        # Step 2: Create JSON mapping and ingest sample data
        logging.info("\nCreating JSON mapping and ingesting sample data...")
        create_json_mapping(
            client=client,
            database_name="NetDefaultDB",
            table_name="Users",
            schema=schema,
        )

        sample_data = [
            {
                "Name": "Alice Johnson",
                "Age": 28,
                "Email": "alice@example.com",
                "JoinDate": "2023-01-15T10:30:00Z",
            },
            {
                "Name": "Bob Smith",
                "Age": 35,
                "Email": "bob@example.com",
                "JoinDate": "2022-06-20T14:45:00Z",
            },
            {
                "Name": "Charlie Brown",
                "Age": 22,
                "Email": "charlie@example.com",
                "JoinDate": "2024-03-10T09:15:00Z",
            },
            {
                "Name": "Diana Prince",
                "Age": 31,
                "Email": "diana@example.com",
                "JoinDate": "2021-11-05T16:20:00Z",
            },
        ]

        ingest_data_inline(
            client=client,
            database_name="NetDefaultDB",
            table_name="Users",
            data=sample_data,
        )
        logging.info("Sample data ingested successfully!")

        # Step 3: Validate queries against the table
        logging.info("\nValidating queries...")
        properties = ClientRequestProperties()
        # This ensures that any time-dependent queries return consistently
        custom_datetime = datetime(2024, 12, 3, 0, 0, 0)
        properties.set_option("query_now", custom_datetime.isoformat())

        test_queries = [
            ("Get all users", "Users | take 10"),
            ("Count users", "Users | count"),
            ("Filter by age", "Users | where Age > 25"),
            ("Filter by join date", "Users | where JoinDate > ago(365d)"),
            ("Invalid table query", "NonExistentTable | take 10"),
        ]

        result = check_list_queries(client, test_queries, properties)

        logging.info("\nQuery validation results:")
        logging.info(result)

        # Step 4: Clean up by clearing the table
        logging.info("\nCleaning up by clearing the 'Users' table...")
        from kusto_doctor.tables import clear_table

        clear_table(
            client=client,
            database_name="NetDefaultDB",
            table_name="Users",
        )
        logging.info("Table 'Users' cleared successfully!")


if __name__ == "__main__":
    main()
