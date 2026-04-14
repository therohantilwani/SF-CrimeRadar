"""Public data feed ingestion (news, social media, etc.)."""

import httpx
from datetime import datetime, timedelta
from typing import AsyncGenerator, Optional

from .base import DataSource, DataSourceBase, DataSourceType


class PublicDataIngestor(DataSourceBase):
    """Ingests crime-related data from public sources."""

    SOURCE_TYPE = DataSourceType.PUBLIC_FEED

    def __init__(self, source: DataSource):
        super().__init__(source)
        self.client: Optional[httpx.AsyncClient] = None

    async def connect(self) -> bool:
        """Connect to public data API."""
        try:
            self.client = httpx.AsyncClient(
                base_url=self.source.endpoint,
                timeout=30.0,
            )
            return await self.health_check()
        except Exception as e:
            self.logger.error(f"Failed to connect to public feed: {e}")
            return False

    async def health_check(self) -> bool:
        """Verify API connectivity."""
        if not self.client:
            return False
        try:
            response = await self.client.get("/status")
            return response.status_code in (200, 404)
        except Exception:
            return True

    async def fetch_incidents(
        self, since: Optional[datetime] = None
    ) -> AsyncGenerator[dict, None]:
        """Fetch incidents from public sources."""
        if not self.client:
            await self.connect()

        since = since or (datetime.utcnow() - timedelta(hours=6))

        endpoints = ["/crimes", "/incidents", "/reports"]

        for endpoint in endpoints:
            try:
                params = {
                    "after": since.isoformat(),
                    "verified": "true",
                }
                response = await self.client.get(endpoint, params=params)
                response.raise_for_status()

                data = response.json()
                for item in data.get("results", []):
                    if self._verify_incident(item):
                        yield self._normalize_public_incident(item)

            except httpx.HTTPError as e:
                self.logger.warning(f"Error fetching from {endpoint}: {e}")

    def _verify_incident(self, data: dict) -> bool:
        """Verify incident has sufficient location and details."""
        has_location = (
            data.get("latitude") is not None
            and data.get("longitude") is not None
        )
        has_details = bool(data.get("description") or data.get("title"))
        return has_location and has_details

    def _normalize_public_incident(self, raw: dict) -> dict:
        """Convert public source data to standard format."""
        crime_type = self._infer_crime_type(raw.get("description", ""))

        return {
            "incident_number": raw.get("id", f"public-{datetime.utcnow().timestamp()}"),
            "crime_type": crime_type,
            "severity": self._assess_severity(raw),
            "status": "reported",
            "location": {
                "latitude": raw.get("latitude", 0),
                "longitude": raw.get("longitude", 0),
                "address": raw.get("address", ""),
            },
            "coordinates": (raw.get("latitude", 0), raw.get("longitude", 0)),
            "reported_at": raw.get("created_at", datetime.utcnow().isoformat()),
            "description": raw.get("description", ""),
            "source": f"public_{self.source.name}",
            "raw_data": raw,
        }

    def _infer_crime_type(self, description: str) -> str:
        """Infer crime type from description text."""
        desc_lower = description.lower()
        keywords = {
            "theft": ["stolen", "theft", "robbed"],
            "assault": ["assault", "attacked", "beaten"],
            "vandalism": ["vandalized", "graffiti", "damaged"],
            "burglary": ["burglar", "broke in", "home invasion"],
        }
        for crime, words in keywords.items():
            if any(w in desc_lower for w in words):
                return crime
        return "other"

    def _assess_severity(self, raw: dict) -> str:
        """Assess incident severity."""
        verified = raw.get("verified", False)
        has_multiple_sources = raw.get("source_count", 0) > 1

        if verified or has_multiple_sources:
            return "medium"
        return "low"

    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
