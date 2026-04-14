"""Police department data feed ingestion."""

import httpx
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional

from .base import DataSource, DataSourceBase, DataSourceType
from crime_radar.core.models import CrimeIncident, CrimeType, SeverityLevel, IncidentStatus, Location


class PoliceDataIngestor(DataSourceBase):
    """Ingests crime data from police department APIs."""

    SOURCE_TYPE = DataSourceType.POLICE_API

    def __init__(self, source: DataSource):
        super().__init__(source)
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Connect to police department API."""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.source.endpoint,
                headers={"Authorization": f"Bearer {self.source.api_key}"}
                if self.source.api_key
                else {},
                timeout=30.0,
            )
            return await self.health_check()
        except Exception as e:
            self.logger.error(f"Failed to connect to police API: {e}")
            return False

    async def health_check(self) -> bool:
        """Verify API connectivity."""
        if not self.client:
            return False
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return True

    async def fetch_incidents(
        self, since: Optional[datetime] = None
    ) -> AsyncGenerator[dict, None]:
        """Fetch incidents from police blotter."""
        if not self.client:
            await self.connect()

        since = since or (datetime.utcnow() - timedelta(hours=24))

        try:
            params = {"from_date": since.isoformat(), "limit": 1000}
            response = await self.client.get("/incidents", params=params)
            response.raise_for_status()

            data = response.json()
            for item in data.get("incidents", []):
                yield self._normalize_incident(item)

        except httpx.HTTPError as e:
            self.logger.error(f"Error fetching police incidents: {e}")
            self.source.errors += 1

    def _normalize_incident(self, raw: dict) -> dict:
        """Convert raw police data to standard incident format."""
        crime_type = self._map_crime_type(raw.get("nature_of_call", ""))
        severity = self._map_severity(raw.get("priority", ""), crime_type)

        return {
            "incident_number": raw.get("incident_id", ""),
            "crime_type": crime_type,
            "severity": severity,
            "status": IncidentStatus.REPORTED,
            "location": {
                "latitude": raw.get("latitude", 0),
                "longitude": raw.get("longitude", 0),
                "address": raw.get("address", ""),
                "city": raw.get("city", ""),
            },
            "coordinates": (raw.get("latitude", 0), raw.get("longitude", 0)),
            "reported_at": raw.get("call_time", datetime.utcnow().isoformat()),
            "description": raw.get("description", ""),
            "source": f"police_{self.source.name}",
            "raw_data": raw,
        }

    def _map_crime_type(self, nature: str) -> CrimeType:
        """Map call nature to crime type."""
        nature_lower = nature.lower()
        if "theft" in nature_lower or "larceny" in nature_lower:
            return CrimeType.THEFT
        if "burglary" in nature_lower or "break" in nature_lower:
            return CrimeType.BURGLARY
        if "assault" in nature_lower or "battery" in nature_lower:
            return CrimeType.ASSAULT
        if "robbery" in nature_lower or "holdup" in nature_lower:
            return CrimeType.ROBBERY
        if "vandalism" in nature_lower or "destruction" in nature_lower:
            return CrimeType.VANDALISM
        if "drug" in nature_lower or "narcotic" in nature_lower:
            return CrimeType.DRUG_OFFENSE
        if "weapon" in nature_lower or "gun" in nature_lower or "knife" in nature_lower:
            return CrimeType.WEAPONS
        return CrimeType.OTHER

    def _map_severity(self, priority: str, crime_type: CrimeType) -> SeverityLevel:
        """Map priority to severity level."""
        priority_lower = priority.lower()
        if "1" in priority_lower or "urgent" in priority_lower:
            if crime_type in [CrimeType.HOMICIDE, CrimeType.ASSAULT]:
                return SeverityLevel.CRITICAL
            return SeverityLevel.HIGH
        if "2" in priority_lower or "priority" in priority_lower:
            return SeverityLevel.MEDIUM
        return SeverityLevel.LOW

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
