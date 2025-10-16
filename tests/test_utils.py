"""Tests for utility functions."""

from src.kusto_doctor.utils import is_valid_kusto_table_name


def test_valid_table_names():
    """Test that valid table names are accepted."""
    valid_names = [
        "MyTable",
        "Table123",
        "User_Data",
        "T",  # single character
        "ValidTableName_123",
        "CamelCaseTable",
        "snake_case_table",
    ]

    for name in valid_names:
        assert is_valid_kusto_table_name(
            name
        ), f"Expected '{name}' to be valid"


def test_invalid_table_names():
    """Test that invalid table names are rejected."""
    invalid_names = [
        "",  # empty string
        "__reserved__",  # double underscore start/end
        "__internal",  # double underscore start
        "table__",  # double underscore end
        "System Events",  # spaces not allowed
        "table with spaces",  # spaces not allowed
        "log.table",  # dots not allowed
        "data.source-2024",  # dots not allowed
        "table.with.dots",  # dots not allowed
        "app-logs",  # dashes not allowed
        "kebab-case-table",  # dashes not allowed
        "table@name",  # invalid character @
        "table#name",  # invalid character #
        "table$name",  # invalid character $
        "table%name",  # invalid character %
        "table&name",  # invalid character &
        "table*name",  # invalid character *
        "table+name",  # invalid character +
        "table=name",  # invalid character =
        "table[name]",  # invalid characters []
        "table{name}",  # invalid characters {}
        "table|name",  # invalid character |
        "table\\name",  # invalid character \
        "table/name",  # invalid character /
        "table:name",  # invalid character :
        "table;name",  # invalid character ;
        "table<name>",  # invalid characters <>
        'table"name"',  # invalid character "
        "table'name'",  # invalid character '
    ]

    for name in invalid_names:
        assert not is_valid_kusto_table_name(
            name
        ), f"Expected '{name}' to be invalid"


def test_kql_keywords_rejected():
    """Test that KQL keywords are rejected."""
    kql_keywords = [
        "where",
        "project",
        "extend",
        "summarize",
        "count",
        "distinct",
        "join",
        "union",
        "sort",
        "top",
        "limit",
        "take",
        "skip",
        "WHERE",
        "PROJECT",
        "EXTEND",  # uppercase variants
        "Where",
        "Project",
        "Extend",  # mixed case variants
    ]

    for keyword in kql_keywords:
        assert not is_valid_kusto_table_name(
            keyword
        ), f"Expected KQL keyword '{keyword}' to be rejected"


def test_length_constraints():
    """Test table name length constraints."""
    # Test maximum valid length (1024 characters)
    max_valid = "A" * 1024
    assert is_valid_kusto_table_name(
        max_valid
    ), "Expected 1024-character name to be valid"

    # Test exceeding maximum length
    too_long = "A" * 1025
    assert not is_valid_kusto_table_name(
        too_long
    ), "Expected 1025-character name to be invalid"


def test_reserved_patterns():
    """Test that reserved patterns are rejected."""
    reserved_patterns = [
        "__start",
        "end__",
        "__both__",
        "__",
        "___triple___",
    ]

    for pattern in reserved_patterns:
        assert not is_valid_kusto_table_name(
            pattern
        ), f"Expected reserved pattern '{pattern}' to be rejected"


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    # Names containing keywords but not exact matches should be allowed
    containing_keywords = [
        "my_where_table",
        "projectData",
        "summary_extend",
        "whereabouts",
    ]

    for name in containing_keywords:
        assert is_valid_kusto_table_name(
            name
        ), f"Expected '{name}' (contains keyword but isn't exact match) to be valid"

    # Numbers and underscores in various positions
    numeric_cases = [
        "123table",  # starts with number - should be valid
        "table123",  # ends with number
        "tab123le",  # number in middle
        "_table",  # starts with underscore
        "table_",  # ends with underscore
        "_123",  # underscore and number
    ]

    for name in numeric_cases:
        assert is_valid_kusto_table_name(
            name
        ), f"Expected '{name}' to be valid"


def test_unicode_and_special_chars():
    """Test handling of unicode and special characters."""
    # These should be invalid due to non-ASCII characters
    unicode_names = [
        "table名前",  # Japanese characters
        "table_émoji",  # accented characters
        "table🚀",  # emoji
        "tableé",  # accented e
    ]

    for name in unicode_names:
        # Note: The current implementation may accept some Unicode letters
        # depending on the regex. This test documents the expected behavior.
        result = is_valid_kusto_table_name(name)
        # The function should reject non-ASCII characters for security
        assert (
            not result
        ), f"Expected Unicode name '{name}' to be rejected for security"
