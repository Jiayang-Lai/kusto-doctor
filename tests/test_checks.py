import logging
import pathlib
from datetime import datetime

from azure.kusto.data import ClientRequestProperties

from src.kusto_doctor import checks
from src.kusto_doctor.utils import buildKustoClient


def test_check_directory_queries(caplog):
    caplog.set_level(logging.INFO)
    current_dir = pathlib.Path(__file__).parent.resolve()
    mock_query_dir = current_dir / "detections"
    logging.info(f"Using mock query directory: {mock_query_dir}")

    properties = ClientRequestProperties()
    # https://learn.microsoft.com/en-us/kusto/api/rest/request-properties?view=microsoft-fabric#:~:text=allowed%20to%20produce.-,query_now,-datetime
    # Use query_now to ensure the in-query datetime is fixed to specific time.
    custom_datetime = datetime(2024, 10, 30, 0, 0, 0)
    properties.set_option("query_now", custom_datetime.isoformat())
    with buildKustoClient() as client:
        result = checks.check_directory_queries(client, mock_query_dir, properties)
        assert len(result["success"]) == 2
        success_keys = ["ValidKqlDetection", "LookBack"]
        for key in success_keys:
            assert key in result["success"]
        assert len(result["errors"]) == 2
        error_keys = ["InvalidKqlDetection", "InvalidDefenderDetection"]
        for key in error_keys:
            assert key in result["errors"]
        return
    raise AssertionError()
