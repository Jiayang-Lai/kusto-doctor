"""Test cases for queries.py module."""

import logging
import os
import pathlib
import tempfile
from unittest.mock import MagicMock, patch

from src.kusto_doctor.exceptions import SourceLoadError
from src.kusto_doctor.queries import (
    extract_queries_from_directory,
    extract_queries_from_list,
)


def get_test_detections_dir():
    """Get the test detections directory path."""
    current_dir = pathlib.Path(__file__).parent.resolve()
    return os.path.join(current_dir, "detections")


def test_extract_queries_with_valid_directory(caplog):
    """Test extracting queries from a valid directory with sentinel and defender detections."""  # noqa: E501
    caplog.set_level(logging.INFO)

    test_detections_dir = get_test_detections_dir()
    queries = extract_queries_from_directory(test_detections_dir)

    # Should have queries from both sentinel and defender directories
    assert len(queries) > 0

    # Check that we have tuples with (detection_name, query_text)
    for detection_name, query_text in queries:
        assert isinstance(detection_name, str)
        assert isinstance(query_text, str)
        assert len(detection_name) > 0
        assert len(query_text) > 0

    # Check that logging occurred
    assert "Using provided detection directory:" in caplog.text
    assert "Collected" in caplog.text and "queries" in caplog.text


def test_extract_queries_with_none_directory(caplog):
    """Test extracting queries when no directory is provided."""
    caplog.set_level(logging.WARNING)

    queries = extract_queries_from_directory(None)

    assert queries == []
    assert "No detection directory provided." in caplog.text


def test_extract_queries_with_empty_string_directory(caplog):
    """Test extracting queries with empty string directory."""
    caplog.set_level(logging.WARNING)

    queries = extract_queries_from_directory("")

    assert queries == []
    assert "No detection directory provided." in caplog.text


def test_extract_queries_with_nonexistent_directory(caplog):
    """Test extracting queries from a nonexistent directory."""
    caplog.set_level(logging.INFO)

    nonexistent_dir = "/path/that/does/not/exist"

    # This should not raise an exception but return empty list
    # The DirectoryQuerySource will handle the missing directories gracefully
    queries = extract_queries_from_directory(nonexistent_dir)

    # Should be empty since directories don't exist
    assert queries == []
    assert f"Using provided detection directory: {nonexistent_dir}" in caplog.text


def test_extract_queries_with_temp_directory_structure(caplog):
    """Test with a temporary directory structure to ensure proper behavior."""
    caplog.set_level(logging.INFO)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sentinel directory with a test detection
        sentinel_dir = pathlib.Path(temp_dir) / "sentinel"
        sentinel_dir.mkdir()

        test_detection = {
            "properties": {"query": "TestTable | where Column == 'value'"}
        }

        with open(sentinel_dir / "test_detection.json", "w") as f:
            import json

            json.dump(test_detection, f)

        # Create defender directory (empty for this test)
        defender_dir = pathlib.Path(temp_dir) / "defender"
        defender_dir.mkdir()

        queries = extract_queries_from_directory(temp_dir)

        assert len(queries) == 1
        detection_name, query_text = queries[0]
        assert detection_name == "test_detection"
        assert query_text == "TestTable | where Column == 'value'"


@patch("src.kusto_doctor.queries.DirectoryQuerySource")
def test_extract_queries_with_mocked_source(mock_source_class, caplog):
    """Test with mocked DirectoryQuerySource to verify interaction."""
    caplog.set_level(logging.INFO)

    # Create mock instances
    mock_sentinel_source = MagicMock()
    mock_defender_source = MagicMock()

    # Configure the mock to return different instances for different calls
    mock_source_class.side_effect = [
        mock_sentinel_source,
        mock_defender_source,
    ]

    # Configure the load_queries method to return test data
    mock_sentinel_source.load_queries.return_value = [
        ("sentinel_detection", "sentinel query text")
    ]
    mock_defender_source.load_queries.return_value = [
        ("defender_detection", "defender query text")
    ]

    test_dir = "/test/dir"
    queries = extract_queries_from_directory(test_dir)

    # Verify the sources were created with correct parameters
    assert mock_source_class.call_count == 2

    # Check first call (sentinel)
    sentinel_call_args = mock_source_class.call_args_list[0]
    assert str(sentinel_call_args[0][0]).endswith("sentinel")
    assert sentinel_call_args[0][1] == ["properties", "query"]

    # Check second call (defender)
    defender_call_args = mock_source_class.call_args_list[1]
    assert str(defender_call_args[0][0]).endswith("defender")
    assert defender_call_args[0][1] == ["queryCondition", "queryText"]

    # Verify results
    assert len(queries) == 2
    assert ("sentinel_detection", "sentinel query text") in queries
    assert ("defender_detection", "defender query text") in queries


@patch("src.kusto_doctor.queries.DirectoryQuerySource")
def test_extract_queries_with_source_error(mock_source_class, caplog):
    """Test behavior when DirectoryQuerySource raises an exception."""
    caplog.set_level(logging.ERROR)

    # Configure mock to raise exception
    mock_source = MagicMock()
    mock_source.load_queries.side_effect = SourceLoadError("Test error")
    mock_source_class.return_value = mock_source

    # The function should handle the exception gracefully and return empty list
    queries = extract_queries_from_directory("/test/dir")

    # Should return empty list when source errors occur
    assert queries == []

    # Should log the error
    assert any(
        "error" in record.message.lower() or "failed" in record.message.lower()
        for record in caplog.records
    ), "Expected error to be logged"


def test_extract_queries_real_test_data(caplog):
    """Test with the actual test detection files to verify expected behavior."""  # noqa: E501
    caplog.set_level(logging.INFO)

    test_detections_dir = get_test_detections_dir()
    queries = extract_queries_from_directory(test_detections_dir)

    # We should have queries from the test detection files
    query_names = [name for name, _ in queries]

    # Check for specific test files we know exist
    expected_detections = [
        "ValidKqlDetection",
        "InvalidKqlDetection",
        "LookBack",
        "InvalidDefenderDetection",
    ]

    for expected in expected_detections:
        assert expected in query_names, (
            f"Expected detection '{expected}' not found in results"
        )

    # Verify query content is not empty
    for name, query in queries:
        assert query.strip() != "", f"Query for detection '{name}' should not be empty"


def test_extract_queries_directory_navigator_paths():
    """Test that the correct navigator paths are used for sentinel and defender."""
    # This is more of an integration test to ensure the paths work correctly
    test_detections_dir = get_test_detections_dir()
    queries = extract_queries_from_directory(test_detections_dir)

    # Find a sentinel query (should be extracted using properties.query path)
    sentinel_queries = []
    defender_queries = []

    # We can infer which are sentinel or defender
    # based on the test file structure
    # and the content we know exists in the test files
    for name, query in queries:
        if (
            "AuditLogs" in query or "ago(7d)" in query
        ):  # Characteristics of sentinel test data
            sentinel_queries.append((name, query))
        elif (
            "DeviceNetworkEvents" in query or "ago(1h)" in query
        ):  # Characteristics of defender test data
            defender_queries.append((name, query))

    # Verify we found both types
    assert len(sentinel_queries) > 0, "Should have found sentinel queries"
    assert len(defender_queries) > 0, "Should have found defender queries"


def test_extract_queries_with_directory_containing_only_files():
    """Test with a directory that doesn't have sentinel/defender subdirectories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a file directly in the temp directory (no subdirectories)
        with open(pathlib.Path(temp_dir) / "some_file.json", "w") as f:
            f.write('{"test": "data"}')

        queries = extract_queries_from_directory(temp_dir)

        # Should return empty list since no sentinel/defender subdirs exist
        assert queries == []


def test_extract_queries_logging_behavior(caplog):
    """Test that logging behaves correctly in different scenarios."""
    caplog.set_level(logging.INFO)

    # Test with valid directory
    test_detections_dir = get_test_detections_dir()

    queries = extract_queries_from_directory(test_detections_dir)

    # Check logging messages
    log_messages = [record.message for record in caplog.records]

    # Should log the directory being used
    assert any("Using provided detection directory:" in msg for msg in log_messages)

    # Should log the count of collected queries
    assert any("Collected" in msg and "queries" in msg for msg in log_messages)

    # Verify the count in the log matches actual results
    count_log = [
        msg for msg in log_messages if "Collected" in msg and "queries" in msg
    ][0]
    expected_count = len(queries)
    assert str(expected_count) in count_log


def test_extract_queries_from_list_with_valid_data(caplog):
    """Test extracting queries from a valid list of detection tuples."""
    caplog.set_level(logging.INFO)

    detection_list = [
        ("detection1", "Table1 | where Column == 'value1'"),
        ("detection2", "Table2 | summarize count() by Category"),
        ("detection3", "SecurityEvent | where EventID == 4624"),
    ]

    queries = extract_queries_from_list(detection_list)

    assert len(queries) == 3

    # Verify the queries are returned as-is
    for i, (name, query) in enumerate(queries):
        expected_name, expected_query = detection_list[i]
        assert name == expected_name
        assert query == expected_query

    # Check logging
    assert "Extracted 3 queries from provided list." in caplog.text


def test_extract_queries_from_list_with_empty_list(caplog):
    """Test extracting queries from an empty list."""
    caplog.set_level(logging.WARNING)

    queries = extract_queries_from_list([])

    assert queries == []
    assert "No detections provided." in caplog.text


def test_extract_queries_from_list_with_none(caplog):
    """Test extracting queries when None is provided."""
    caplog.set_level(logging.WARNING)

    queries = extract_queries_from_list(None)

    assert queries == []
    assert "No detections provided." in caplog.text


def test_extract_queries_from_list_with_single_detection(caplog):
    """Test extracting queries from a list with a single detection."""
    caplog.set_level(logging.INFO)

    detection_list = [("single_detection", "AuditLogs | take 10")]

    queries = extract_queries_from_list(detection_list)

    assert len(queries) == 1
    assert queries[0] == ("single_detection", "AuditLogs | take 10")
    assert "Extracted 1 queries from provided list." in caplog.text


def test_extract_queries_from_list_with_empty_strings(caplog):
    """Test extracting queries with empty detection names or queries."""
    caplog.set_level(logging.INFO)

    detection_list = [
        ("", "Table | where Column == 'value'"),
        ("detection_with_empty_query", ""),
        ("normal_detection", "Table | count"),
    ]

    queries = extract_queries_from_list(detection_list)

    # Should still process all entries, including empty strings
    assert len(queries) == 3
    assert queries[0] == ("", "Table | where Column == 'value'")
    assert queries[1] == ("detection_with_empty_query", "")
    assert queries[2] == ("normal_detection", "Table | count")


def test_extract_queries_from_list_with_special_characters(caplog):
    """Test extracting queries with special characters in names and queries."""
    caplog.set_level(logging.INFO)

    detection_list = [
        (
            "detection-with-dashes",
            "Table | where Column contains 'test-value'",
        ),
        (
            "detection_with_unicode_😀",
            "Table | where Message contains 'émoji'",
        ),
        (
            "detection.with.dots",
            "Table | where Path contains 'C:\\Windows\\System32'",
        ),
    ]

    queries = extract_queries_from_list(detection_list)

    assert len(queries) == 3

    # Verify special characters are preserved
    assert queries[0][0] == "detection-with-dashes"
    assert queries[1][0] == "detection_with_unicode_😀"
    assert queries[2][0] == "detection.with.dots"
    assert "C:\\Windows\\System32" in queries[2][1]


@patch("src.kusto_doctor.queries.logger")
def test_extract_queries_from_list_with_invalid_tuple_structure(mock_logger, caplog):
    """Test behavior when list contains invalid tuple structures."""
    caplog.set_level(logging.ERROR)

    # This would cause an exception when trying to unpack
    invalid_detection_list = [
        ("valid_detection", "valid query"),
        ("single_element",),  # Invalid - only one element
        ("too", "many", "elements"),  # Invalid - too many elements
    ]

    # The function should handle this gracefully and log errors
    _ = extract_queries_from_list(invalid_detection_list)

    # Should process the valid detection and handle errors for invalid ones
    # The exact behavior depends on implementation, but errors should be logged
    assert mock_logger.error.called


def test_extract_queries_from_list_with_large_dataset():
    """Test extracting queries from a large list to verify performance."""
    # Generate a large list of detections
    large_detection_list = [
        (f"detection_{i}", f"Table{i} | where Column == 'value{i}'")
        for i in range(1000)
    ]

    queries = extract_queries_from_list(large_detection_list)

    assert len(queries) == 1000

    # Spot check a few entries
    assert queries[0] == ("detection_0", "Table0 | where Column == 'value0'")
    assert queries[500] == (
        "detection_500",
        "Table500 | where Column == 'value500'",
    )
    assert queries[999] == (
        "detection_999",
        "Table999 | where Column == 'value999'",
    )


def test_extract_queries_from_list_preserves_order():
    """Test that the function preserves the order of the input list."""
    detection_list = [
        ("z_detection", "last query"),
        ("a_detection", "first query"),
        ("m_detection", "middle query"),
    ]

    queries = extract_queries_from_list(detection_list)

    # Order should be preserved, not alphabetical
    assert queries[0][0] == "z_detection"
    assert queries[1][0] == "a_detection"
    assert queries[2][0] == "m_detection"


def test_extract_queries_from_list_with_multiline_queries(caplog):
    """Test extracting queries that span multiple lines."""
    caplog.set_level(logging.INFO)

    multiline_query = """SecurityEvent
| where TimeGenerated > ago(24h)
| where EventID == 4624
| summarize count() by Account"""

    detection_list = [
        ("multiline_detection", multiline_query),
        ("single_line", "Table | count"),
    ]

    queries = extract_queries_from_list(detection_list)

    assert len(queries) == 2
    assert queries[0][1] == multiline_query
    assert "\n" in queries[0][1]  # Verify newlines are preserved


def test_extract_queries_from_list_logging_behavior(caplog):
    """Test the logging behavior of extract_queries_from_list."""
    caplog.set_level(logging.INFO)

    detection_list = [("det1", "query1"), ("det2", "query2")]

    queries = extract_queries_from_list(detection_list)

    # Check that the correct log message is generated
    log_messages = [record.message for record in caplog.records]
    assert any("Extracted 2 queries from provided list." in msg for msg in log_messages)

    # Verify the count in the log matches actual results
    assert len(queries) == 2
