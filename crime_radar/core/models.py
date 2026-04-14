"""Data models for the crime radar platform."""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class CrimeType(str, Enum):
    """Types of criminal activities."""

    THEFT = "theft"
    BURGLARY = "burglary"
    ASSAULT = "assault"
    ROBBERY = "robbery"
    VANDALISM = "vandalism"
    DRUG_OFFENSE = "drug_offense"
    WEAPONS = "weapons"
    SEXUAL_OFFENSE = "sexual_offense"
    HOMICIDE = "homicide"
    ARSON = "arson"
    FRAUD = "fraud"
    OTHER = "other"


class SeverityLevel(str, Enum):
    """Crime severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IncidentStatus(str, Enum):
    """Status of a crime incident."""

    REPORTED = "reported"
    INVESTIGATING = "investigating"
    UNDER_REVIEW = "under_review"
    CLOSED = "closed"
    UNSOLVED = "unsolved"


class RiskLevel(str, Enum):
    """Zone risk levels."""

    SAFE = "safe"
    LOW = "low"
    MODERATE = "moderate"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


class Location(BaseModel):
    """Geographic location."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = "US"


class CrimeIncident(BaseModel):
    """Model for a crime incident."""

    id: UUID = Field(default_factory=uuid4)
    incident_number: str
    crime_type: CrimeType
    severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.REPORTED

    location: Location
    coordinates: tuple[float, float]  # (lat, lon)

    reported_at: datetime
    occurred_from: Optional[datetime] = None
    occurred_to: Optional[datetime] = None

    description: Optional[str] = None
    weapons_involved: bool = False
    injuries_reported: bool = False

    victim_count: int = 0
    suspect_count: int = 0

    source: str  # e.g., "police_blotter", "911_calls", "iot_sensor"
    source_id: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Zone(BaseModel):
    """Geographic zone for risk assessment."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    zone_type: str  # grid, neighborhood, district, custom

    coordinates: list[tuple[float, float]]  # polygon points

    risk_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: RiskLevel = RiskLevel.SAFE

    population: int = 0
    area_sq_km: float = 0.0

    incident_count_24h: int = 0
    incident_count_7d: int = 0
    incident_count_30d: int = 0

    dominant_crime_types: list[CrimeType] = []
    trend_direction: str = "stable"  # increasing, decreasing, stable

    last_updated: datetime = Field(default_factory=datetime.utcnow)


class PatternDetection(BaseModel):
    """Detected crime pattern."""

    id: UUID = Field(default_factory=uuid4)
    pattern_type: str  # serial_incidents, hotspot, temporal, behavioral

    confidence_score: float = Field(..., ge=0, le=1)

    description: str
    involved_incidents: list[UUID] = []

    geographic_radius_km: float = 0.0
    temporal_span_hours: float = 0.0

    predicted_next_incident: Optional[dict] = None

    detected_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed: bool = False


class Alert(BaseModel):
    """Security alert."""

    id: UUID = Field(default_factory=uuid4)
    alert_type: str  # pattern_detected, risk_increase, anomaly
    severity: SeverityLevel

    title: str
    message: str

    zone_id: Optional[UUID] = None
    related_incidents: list[UUID] = []
    related_patterns: list[UUID] = []

    actionable: bool = True
    recommended_actions: list[str] = []

    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class DataSource(BaseModel):
    """Data source configuration."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    source_type: str  # police_api, iot, public_feed, manual

    endpoint: Optional[str] = None
    api_key: Optional[str] = None

    enabled: bool = True
    polling_interval_seconds: int = 300

    last_sync: Optional[datetime] = None
    records_synced: int = 0
    errors: int = 0

    created_at: datetime = Field(default_factory=datetime.utcnow)
