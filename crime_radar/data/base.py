"""Base data source classes and interfaces."""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import AsyncGenerator, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field
import loguru


class DataSourceType(str, Enum):
    """Types of data sources."""

    POLICE_API = "police_api"
    IOT_SENSOR = "iot_sensor"
    PUBLIC_FEED = "public_feed"
    911_DISPATCH = "911_dispatch"
    SOCIAL_MEDIA = "social_media"
    MANUAL_INPUT = "manual_input"


class DataSource(BaseModel):
    """Configuration for a data source."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: DataSourceType
    enabled: bool = True
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    polling_interval_seconds: int = 300
    last_sync: Optional[datetime] = None
    records_synced: int = 0
    errors: int = 0


class DataSourceBase(ABC):
    """Abstract base class for data ingestors."""

    def __init__(self, source: DataSource, logger: Optional[loguru.Logger] = None):
        self.source = source
        self.logger = logger or loguru.logger

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the data source."""
        pass

    @abstractmethod
    async def fetch_incidents(
        self, since: Optional[datetime] = None
    ) -> AsyncGenerator[dict, None]:
        """Fetch new incidents from the source."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is healthy."""
        pass

    async def disconnect(self) -> None:
        """Close connection to the data source."""
        pass
