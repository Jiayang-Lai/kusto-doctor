"""Unit tests for Kusto Doctor checks module."""

import logging
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from azure.kusto.data import ClientRequestProperties
from azure.kusto.data.exceptions import KustoServiceError

from src.kusto_doctor import checks


def test_check_single_query_success(caplog):
    """Test check_single_query with a successful query execution."""
    caplog.set_level(logging.INFO)

    # Mock client and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_result_table = MagicMock()

    # Configure mock to simulate successful execution
    mock_client.execute.return_value = mock_response
    mock_response.primary_results = [mock_result_table]

    # Mock non-empty result
    mock_result_table.__len__.return_value = 1

    with patch(
        "src.kusto_doctor.checks.dataframe_from_result_table"
    ) as mock_df_converter:
        mock_df = pd.DataFrame({"col1": [1, 2, 3]})
        mock_df_converter.return_value = mock_df

        properties = ClientRequestProperties()
        result_df, error = checks.check_single_query(
            mock_client,
            "test_query",
            "TestTable | count",
            properties,
            "test_db",
        )

        # Verify success
        assert error is None
        assert isinstance(result_df, pd.DataFrame)
        assert result_df.equals(mock_df)

        # Verify client was called correctly
        mock_client.execute.assert_called_once_with(
            "test_db", "TestTable | count", properties
        )

        # Verify logging
        assert "Query test_query ran successfully." in caplog.text


def test_check_single_query_success_empty_result(caplog):
    """Test check_single_query with successful execution but empty result."""
    caplog.set_level(logging.INFO)

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_result_table = MagicMock()

    # Configure mock for empty result
    mock_client.execute.return_value = mock_response
    mock_response.primary_results = [mock_result_table]
    mock_result_table.__len__.return_value = 0

    properties = ClientRequestProperties()
    result_df, error = checks.check_single_query(
        mock_client, "empty_query", "TestTable | where 1 == 0", properties
    )

    # Should succeed but return None DataFrame for empty results
    assert error is None
    assert result_df is None
    assert "Query empty_query ran successfully." in caplog.text


def test_check_single_query_kusto_service_error(caplog):
    """Test check_single_query with KustoServiceError."""
    caplog.set_level(logging.ERROR)

    mock_client = MagicMock()
    error_message = "Syntax error: Invalid query syntax"
    mock_client.execute.side_effect = KustoServiceError(error_message)

    properties = ClientRequestProperties()
    result_df, error = checks.check_single_query(
        mock_client, "invalid_query", "INVALID SYNTAX", properties
    )

    # Should return error
    assert result_df is None
    assert error == error_message
    assert "Query invalid_query failed:" in caplog.text
    assert error_message in caplog.text


def test_check_single_query_with_default_database():
    """Test check_single_query uses default database when not specified."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_result_table = MagicMock()

    mock_client.execute.return_value = mock_response
    mock_response.primary_results = [mock_result_table]
    mock_result_table.__len__.return_value = 0

    properties = ClientRequestProperties()

    # Don't specify database_name to test default
    checks.check_single_query(mock_client, "test", "query", properties)

    # Should use DEFAULT_DATABASE_NAME
    from src.kusto_doctor.constants import DEFAULT_DATABASE_NAME

    mock_client.execute.assert_called_once_with(
        DEFAULT_DATABASE_NAME, "query", properties
    )


def test_check_list_queries_success(caplog):
    """Test check_list_queries with successful queries."""
    caplog.set_level(logging.INFO)

    mock_client = MagicMock()

    detection_list = [
        ("query1", "Table1 | count"),
        ("query2", "Table2 | count"),
    ]

    with patch("src.kusto_doctor.checks.check_single_query") as mock_check:
        # Mock successful results
        mock_df1 = pd.DataFrame({"count": [10]})
        mock_df2 = pd.DataFrame({"count": [20]})

        mock_check.side_effect = [
            (mock_df1, None),  # First query succeeds
            (mock_df2, None),  # Second query succeeds
        ]

        properties = ClientRequestProperties()
        results = checks.check_list_queries(mock_client, detection_list, properties)

        # Verify results structure
        assert "success" in results
        assert "errors" in results
        assert len(results["success"]) == 2
        assert len(results["errors"]) == 0

        # Verify successful queries
        assert "query1" in results["success"]
        assert "query2" in results["success"]
        assert results["success"]["query1"].equals(mock_df1)
        assert results["success"]["query2"].equals(mock_df2)

        # Verify check_single_query was called correctly
        assert mock_check.call_count == 2


def test_check_list_queries_with_errors(caplog):
    """Test check_list_queries with some queries failing."""
    caplog.set_level(logging.ERROR)

    mock_client = MagicMock()

    detection_list = [
        ("success_query", "Table | count"),
        ("error_query", "INVALID SYNTAX"),
        ("another_success", "Table | take 1"),
    ]

    with patch("src.kusto_doctor.checks.check_single_query") as mock_check:
        mock_df = pd.DataFrame({"count": [5]})

        mock_check.side_effect = [
            (mock_df, None),  # First query succeeds
            (None, "Syntax error"),  # Second query fails
            (mock_df, None),  # Third query succeeds
        ]

        results = checks.check_list_queries(mock_client, detection_list)

        # Verify mixed results
        assert len(results["success"]) == 2
        assert len(results["errors"]) == 1

        assert "success_query" in results["success"]
        assert "another_success" in results["success"]
        assert "error_query" in results["errors"]
        assert results["errors"]["error_query"] == "Syntax error"


def test_check_list_queries_empty_list():
    """Test check_list_queries with empty detection list."""
    mock_client = MagicMock()

    with patch("src.kusto_doctor.checks.extract_queries_from_list") as mock_extract:
        mock_extract.return_value = []

        results = checks.check_list_queries(mock_client, [])

        assert results == {"success": {}, "errors": {}}
        mock_extract.assert_called_once_with([])


@patch("src.kusto_doctor.checks.extract_queries_from_list")
def test_check_list_queries_extraction_error(mock_extract):
    """Test check_list_queries when query extraction fails."""
    mock_client = MagicMock()

    # Mock extraction returning empty list (simulating extraction failure)
    mock_extract.return_value = []

    detection_list = [("test", "query")]
    results = checks.check_list_queries(mock_client, detection_list)

    assert results == {"success": {}, "errors": {}}
    mock_extract.assert_called_once_with(detection_list)


def test_check_list_queries_with_none_properties():
    """Test check_list_queries with None query_properties."""
    mock_client = MagicMock()

    detection_list = [("test_query", "Table | count")]

    with patch("src.kusto_doctor.checks.check_single_query") as mock_check:
        mock_check.return_value = (None, None)

        # Should handle None properties gracefully
        _ = checks.check_list_queries(mock_client, detection_list, None, None)

        # Verify check_single_query was called with None properties
        mock_check.assert_called_once_with(
            mock_client, "test_query", "Table | count", None, None
        )


def test_check_list_queries_integration():
    """Integration test for check_list_queries with real query extraction."""
    mock_client = MagicMock()

    detection_list = [
        ("valid_query", "print 'hello'"),
        ("another_valid", "range x from 1 to 3 step 1"),
    ]

    with patch("src.kusto_doctor.checks.check_single_query") as mock_check:
        mock_df = pd.DataFrame({"result": ["test"]})
        mock_check.return_value = (mock_df, None)

        results = checks.check_list_queries(mock_client, detection_list)

        # Should process both queries
        assert len(results["success"]) == 2
        assert "valid_query" in results["success"]
        assert "another_valid" in results["success"]


@pytest.mark.parametrize(
    "query_name,query,expected_calls",
    [
        ("simple", "Table | count", 1),
        ("complex", "Table | where Col == 'value' | summarize count()", 1),
        ("multiline", "Table\n| where Col == 'test'\n| count", 1),
    ],
)
def test_check_single_query_parametrized(query_name, query, expected_calls):
    """Parametrized test for different query types."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_result_table = MagicMock()

    mock_client.execute.return_value = mock_response
    mock_response.primary_results = [mock_result_table]
    mock_result_table.__len__.return_value = 0

    properties = ClientRequestProperties()
    checks.check_single_query(mock_client, query_name, query, properties)

    assert mock_client.execute.call_count == expected_calls
