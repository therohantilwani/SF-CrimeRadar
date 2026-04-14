"""Data ingestion layer for aggregating crime data from multiple sources."""

from .base import DataSource, DataSourceType
from .police_feed import PoliceDataIngestor
from .iot_sensor import IoTDataIngestor
from .public_feed import PublicDataIngestor

__all__ = [
    "DataSource",
    "DataSourceType",
    "PoliceDataIngestor",
    "IoTDataIngestor",
    "PublicDataIngestor",
]
