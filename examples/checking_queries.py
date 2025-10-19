import logging
import pathlib
from datetime import datetime

from azure.kusto.data import ClientRequestProperties

from kusto_doctor.checks import check_directory_queries, check_list_queries
from kusto_doctor.logging import configure_logging
from kusto_doctor.utils import buildKustoClient

logging.basicConfig(level=logging.INFO)


def run_checks_from_directory():
    configure_logging(console_output=False)
    current_dir = pathlib.Path(__file__).parent.parent.resolve()
    mock_query_dir = current_dir / "tests" / "detections"
    with buildKustoClient() as client:
        properties = ClientRequestProperties()
        # Use query_now to ensure the in-query now is fixed to specific time.
        custom_datetime = datetime(2024, 10, 30, 0, 0, 0)
        properties.set_option("query_now", custom_datetime.isoformat())
        result = check_directory_queries(client, mock_query_dir, properties)
    logging.info("Directory check result:")
    logging.info(result)


def run_checks_from_list():
    configure_logging(console_output=False)
    with buildKustoClient() as client:
        properties = ClientRequestProperties()
        test_queries = [
            ("this is a valid query", "AuditLogs | take 10"),
            ("this is an invalid query", "SigninLogs | take 10"),
        ]
        result = check_list_queries(client, test_queries, properties)
    logging.info("List check result:")
    logging.info(result)


if __name__ == "__main__":
    run_checks_from_directory()
    run_checks_from_list()
