import logging
import os
import pathlib

from src.kusto_doctor import ingestions


def test_ingest(caplog):
    caplog.set_level(logging.INFO)
    current_dir = pathlib.Path(__file__).parent.resolve()
    mock_query_dir = os.path.join(current_dir, "sampledata")
    logging.info(f"Using mock query directory: {mock_query_dir}")
    ingestions.load_tables_from_directory(mock_query_dir, "NetDefaultDB")
    assert True
