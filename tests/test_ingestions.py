"""Unit tests for Kusto Doctor ingestions module."""
from unittest.mock import Mock

import pytest

from src.kusto_doctor import ingestions
from src.kusto_doctor.models import ColumnSchema, KustoDataType


def test_create_json_mapping_valid_table():
    """Test creating JSON mapping for a valid table."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "ValidTable"
    schema = [
        ColumnSchema(ColumnName="Name", ColumnType=KustoDataType.string),
        ColumnSchema(ColumnName="Age", ColumnType=KustoDataType.int),
        ColumnSchema(ColumnName="CreatedDate", ColumnType=KustoDataType.datetime),
    ]

    ingestions.create_json_mapping(mock_client, database_name, table_name, schema)

    # Verify that execute_mgmt was called
    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    assert call_args[0][0] == database_name
    assert "JsonMapping" in call_args[0][1]
    assert table_name in call_args[0][1]
    assert "Name" in call_args[0][1]
    assert "Age" in call_args[0][1]
    assert "CreatedDate" in call_args[0][1]


def test_create_json_mapping_invalid_table_name():
    """Test that invalid table names are rejected in create_json_mapping."""
    mock_client = Mock()
    database_name = "TestDB"
    invalid_table_name = "table with spaces"
    schema = [
        ColumnSchema(ColumnName="Name", ColumnType=KustoDataType.string),
    ]

    with pytest.raises(ValueError, match="Invalid Kusto table name"):
        ingestions.create_json_mapping(
            mock_client, database_name, invalid_table_name, schema
        )


def test_ingest_data_inline_valid_data():
    """Test inline data ingestion with valid data."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Users"
    data = [
        {"Name": "Alice", "Age": 30},
        {"Name": "Bob", "Age": 25},
        {"Name": "Charlie", "Age": 35},
    ]

    ingestions.ingest_data_inline(mock_client, database_name, table_name, data)

    # Verify that execute_mgmt was called
    mock_client.execute_mgmt.assert_called()
    call_args = mock_client.execute_mgmt.call_args
    assert database_name in call_args[0]
    assert table_name in call_args[0][1]
    assert ".ingest inline" in call_args[0][1]


def test_ingest_data_inline_invalid_table_name():
    """Test that invalid table names are rejected in ingest_data_inline."""
    mock_client = Mock()
    database_name = "TestDB"
    invalid_table_name = "__reserved__"
    data = [{"Name": "Alice"}]

    with pytest.raises(ValueError, match="Invalid Kusto table name"):
        ingestions.ingest_data_inline(
            mock_client, database_name, invalid_table_name, data
        )


def test_ingest_data_inline_custom_mapping():
    """Test inline data ingestion with custom mapping name."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Users"
    data = [{"Name": "Alice"}]
    custom_mapping = "CustomMapping"

    ingestions.ingest_data_inline(
        mock_client, database_name, table_name, data, mapping_name=custom_mapping
    )

    mock_client.execute_mgmt.assert_called()
    call_args = mock_client.execute_mgmt.call_args
    assert custom_mapping in call_args[0][1]


def test_ingest_data_inline_batch_size():
    """Test inline data ingestion with custom batch size."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Users"
    # Create data larger than batch size
    data = [{"Name": f"User{i}", "Age": 20 + i} for i in range(150)]
    batch_size = 50

    ingestions.ingest_data_inline(
        mock_client, database_name, table_name, data, batch_size=batch_size
    )

    # Should be called 3 times (150 records / 50 batch size)
    assert mock_client.execute_mgmt.call_count == 3


def test_ingest_data_inline_empty_data():
    """Test inline data ingestion with empty data list."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Users"
    data = []

    ingestions.ingest_data_inline(mock_client, database_name, table_name, data)

    # Should not call execute_mgmt for empty data
    mock_client.execute_mgmt.assert_not_called()


def test_ingest_csv_data_from_storage_valid():
    """Test CSV data ingestion from storage."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Logs"
    source = "/path/to/data.csv"

    ingestions.ingest_csv_data_from_storage(
        mock_client, database_name, table_name, source
    )

    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    assert database_name in call_args[0]
    assert table_name in call_args[0][1]
    assert source in call_args[0][1]
    assert "format='csv'" in call_args[0][1]
    assert "ignoreFirstRecord=true" in call_args[0][1]


def test_ingest_csv_data_from_storage_no_header():
    """Test CSV data ingestion from storage without header."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Logs"
    source = "/path/to/data.csv"

    ingestions.ingest_csv_data_from_storage(
        mock_client, database_name, table_name, source, ignore_first_record=False
    )

    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    assert "ignoreFirstRecord=false" in call_args[0][1]


def test_ingest_csv_data_from_storage_invalid_table_name():
    """Test that invalid table names are rejected in CSV ingestion."""
    mock_client = Mock()
    database_name = "TestDB"
    invalid_table_name = "table-with-dashes"
    source = "/path/to/data.csv"

    with pytest.raises(ValueError, match="Invalid Kusto table name"):
        ingestions.ingest_csv_data_from_storage(
            mock_client, database_name, invalid_table_name, source
        )


def test_ingest_json_data_from_storage_valid():
    """Test JSON data ingestion from storage."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Events"
    source = "/path/to/data.json"

    ingestions.ingest_json_data_from_storage(
        mock_client, database_name, table_name, source
    )

    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    assert database_name in call_args[0]
    assert table_name in call_args[0][1]
    assert source in call_args[0][1]
    assert "format='json'" in call_args[0][1]
    assert "JsonMapping" in call_args[0][1]


def test_ingest_json_data_from_storage_custom_mapping():
    """Test JSON data ingestion from storage with custom mapping."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Events"
    source = "/path/to/data.json"
    custom_mapping = "EventMapping"

    ingestions.ingest_json_data_from_storage(
        mock_client, database_name, table_name, source, mapping_name=custom_mapping
    )

    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    assert custom_mapping in call_args[0][1]


def test_ingest_json_data_from_storage_invalid_table_name():
    """Test that invalid table names are rejected in JSON storage ingestion."""
    mock_client = Mock()
    database_name = "TestDB"
    invalid_table_name = "table.with.dots"
    source = "/path/to/data.json"

    with pytest.raises(ValueError, match="Invalid Kusto table name"):
        ingestions.ingest_json_data_from_storage(
            mock_client, database_name, invalid_table_name, source
        )


def test_execute_batch_ingest():
    """Test the private _execute_batch_ingest function."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Users"
    records = '{"Name": "Alice", "Age": 30}\n{"Name": "Bob", "Age": 25}\n'
    mapping_name = "JsonMapping"

    ingestions._execute_batch_ingest(
        mock_client, database_name, table_name, records, mapping_name
    )

    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    assert database_name == call_args[0][0]
    assert table_name in call_args[0][1]
    assert mapping_name in call_args[0][1]
    assert records in call_args[0][1]


def test_ingest_data_inline_with_special_characters():
    """Test inline data ingestion with special characters in data."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "Users"
    data = [
        {"Name": "O'Brien", "Description": 'She said "Hello"'},
        {"Name": "Smith\\Jones", "Description": "Line1\nLine2"},
    ]

    # Should not raise an exception
    ingestions.ingest_data_inline(mock_client, database_name, table_name, data)

    mock_client.execute_mgmt.assert_called()


def test_create_json_mapping_with_various_data_types():
    """Test creating JSON mapping with various Kusto data types."""
    mock_client = Mock()
    database_name = "TestDB"
    table_name = "ComplexTable"
    schema = [
        ColumnSchema(ColumnName="Id", ColumnType=KustoDataType.guid),
        ColumnSchema(ColumnName="IsActive", ColumnType=KustoDataType.bool),
        ColumnSchema(ColumnName="Price", ColumnType=KustoDataType.decimal),
        ColumnSchema(ColumnName="Score", ColumnType=KustoDataType.real),
        ColumnSchema(ColumnName="Count", ColumnType=KustoDataType.long),
        ColumnSchema(ColumnName="Duration", ColumnType=KustoDataType.timespan),
        ColumnSchema(ColumnName="Metadata", ColumnType=KustoDataType.dynamic),
    ]

    ingestions.create_json_mapping(mock_client, database_name, table_name, schema)

    mock_client.execute_mgmt.assert_called_once()
    call_args = mock_client.execute_mgmt.call_args
    command = call_args[0][1]

    # Verify all column names and types are in the command
    for col in schema:
        assert col.ColumnName in command
        assert col.ColumnType.value in command
