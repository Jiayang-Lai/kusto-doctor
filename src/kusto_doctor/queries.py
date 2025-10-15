"""Module for loading Kusto queries from detection files."""

from pathlib import Path
from typing import List, Tuple

from .exceptions import SourceLoadError
from .logging import get_logger
from .sources import DirectoryQuerySource

logger = get_logger()


def extract_queries_from_directory(detection_dir: str = None) -> List[Tuple[str, str]]:
    """Retrieves all queries from <detection_dir>.
    Returns a list of tuples, where the first element is the detection file name,
    and the second element is the query text."""

    queries = []
    if detection_dir:
        logger.info(f"Using provided detection directory: {detection_dir}")
        detection_path = Path(detection_dir)
        sentinel_detection_folder = detection_path / "sentinel"
        defender_detection_folder = detection_path / "defender"
    else:
        logger.warning("No detection directory provided.")
        return []

    # Loading Sentinel detections
    sentinel_query_navigator = ["properties", "query"]
    try:
        sentinel_query_source = DirectoryQuerySource(sentinel_detection_folder, sentinel_query_navigator)
        for detection_name, query in sentinel_query_source.load_queries():
            queries.append((detection_name, query))
    except SourceLoadError as sle:
        logger.error(f"Source load error: {sle}")
    except Exception as e:
        logger.error(f"Failed to load sentinel queries: {e}")

    # Loading Defender detections
    defender_query_navigator = ["queryCondition", "queryText"]
    try:
        defender_query_source = DirectoryQuerySource(defender_detection_folder, defender_query_navigator)
        for detection_name, query in defender_query_source.load_queries():
            queries.append((detection_name, query))
    except SourceLoadError as sle:
        logger.error(f"Source load error: {sle}")
    except Exception as e:
        logger.error(f"Failed to load defender queries: {e}")

    logger.info(f"Collected {len(queries)} queries.")
    return queries
