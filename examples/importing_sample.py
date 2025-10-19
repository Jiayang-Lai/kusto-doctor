import logging

from kusto_doctor.models import ColumnSchema, KustoDataType
from kusto_doctor.tables import create_table
from kusto_doctor.utils import buildKustoClient

logging.basicConfig(level=logging.INFO)


def create_test_table():
    with buildKustoClient() as client:
        test_schema = [
            ColumnSchema(
                ColumnName="QueryName", ColumnType=KustoDataType.string
            ),
            ColumnSchema(ColumnName="Query", ColumnType=KustoDataType.string),
            ColumnSchema(ColumnName="Status", ColumnType=KustoDataType.string),
            ColumnSchema(
                ColumnName="__test__", ColumnType=KustoDataType.string
            ),
        ]
        create_table(
            client=client,
            database_name="NetDefaultDB",
            table_name="thisIsATestTable",
            schema=test_schema,
        )


if __name__ == "__main__":
    create_test_table()
