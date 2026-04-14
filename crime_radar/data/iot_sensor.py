"""IoT sensor data ingestion."""

import asyncio
import json
from datetime import datetime
from typing import AsyncGenerator, Optional
import redis.asyncio as redis

from .base import DataSource, DataSourceBase, DataSourceType


class IoTDataIngestor(DataSourceBase):
    """Ingests data from IoT security sensors (cameras, motion detectors, etc.)."""

    SOURCE_TYPE = DataSourceType.IOT_SENSOR

    def __init__(self, source: DataSource):
        super().__init__(source)
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

    async def connect(self) -> bool:
        """Connect to IoT data stream (Redis/MQTT)."""
        try:
            self.redis_client = redis.from_url(
                self.source.endpoint or "redis://localhost:6379",
                encoding="utf-8",
                decode_responses=True,
            )
            return await self.health_check()
        except Exception as e:
            self.logger.error(f"Failed to connect to IoT stream: {e}")
            return False

    async def health_check(self) -> bool:
        """Check Redis connectivity."""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False

    async def fetch_incidents(
        self, since: Optional[datetime] = None
    ) -> AsyncGenerator[dict, None]:
        """Subscribe to IoT event stream."""
        if not self.redis_client:
            await self.connect()

        self.pubsub = self.redis_client.pubsub()
        channel = f"iot:sensors:{self.source.name}"

        await self.pubsub.subscribe(channel)

        try:
            while True:
                message = await self.pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    data = json.loads(message["data"])
                    if self._is_security_event(data):
                        yield self._normalize_iot_event(data)
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass

    def _is_security_event(self, data: dict) -> bool:
        """Filter for security-relevant IoT events."""
        event_types = {"motion", "intrusion", "door_open", "glass_break", "alarm"}
        return data.get("event_type", "").lower() in event_types

    def _normalize_iot_event(self, raw: dict) -> dict:
        """Convert IoT event to incident format."""
        event_type = raw.get("event_type", "").lower()
        severity = "high" if event_type in ["intrusion", "alarm", "glass_break"] else "medium"

        return {
            "incident_number": f"IOT-{raw.get('sensor_id', 'unknown')}-{int(datetime.utcnow().timestamp())}",
            "crime_type": "other",
            "severity": severity,
            "status": "reported",
            "location": {
                "latitude": raw.get("latitude", 0),
                "longitude": raw.get("longitude", 0),
                "address": raw.get("location_name", ""),
            },
            "coordinates": (raw.get("latitude", 0), raw.get("longitude", 0)),
            "reported_at": raw.get("timestamp", datetime.utcnow().isoformat()),
            "description": f"IoT Event: {event_type} detected by sensor {raw.get('sensor_id', 'unknown')}",
            "source": f"iot_{self.source.name}",
            "raw_data": raw,
        }

    async def disconnect(self) -> None:
        """Close Redis connections."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
