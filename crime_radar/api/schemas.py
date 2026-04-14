"""API request/response schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class LocationSchema(BaseModel):
    """Location schema."""

    latitude: float
    longitude: float
    address: Optional[str] = None


class IncidentCreate(BaseModel):
    """Schema for creating a new incident."""

    crime_type: str
    severity: str
    location: LocationSchema
    reported_at: Optional[datetime] = None
    description: Optional[str] = None
    weapons_involved: bool = False
    injuries_reported: bool = False
    source: str = "manual"


class IncidentResponse(BaseModel):
    """Incident response schema."""

    id: UUID
    incident_number: str
    crime_type: str
    severity: str
    status: str
    location: LocationSchema
    coordinates: tuple[float, float]
    reported_at: datetime
    description: Optional[str] = None
    created_at: datetime


class ZoneRiskResponse(BaseModel):
    """Zone risk response schema."""

    zone_id: UUID
    zone_name: str
    risk_score: float
    risk_level: str
    incident_count_24h: int
    incident_count_7d: int
    dominant_crime_types: list[str]
    trend_direction: str
    hotspots: list[dict] = []
    last_updated: datetime


class AlertResponse(BaseModel):
    """Alert response schema."""

    id: UUID
    alert_type: str
    severity: str
    title: str
    message: str
    zone_id: Optional[UUID] = None
    actionable: bool
    recommended_actions: list[str]
    acknowledged: bool
    created_at: datetime


class PatternResponse(BaseModel):
    """Pattern response schema."""

    id: UUID
    pattern_type: str
    confidence_score: float
    description: str
    involved_incident_count: int
    geographic_radius_km: float
    temporal_span_hours: Optional[float] = None
    predicted_next_incident: Optional[dict] = None
    detected_at: datetime
    confirmed: bool


class DashboardSummary(BaseModel):
    """Dashboard summary response."""

    total_incidents_today: int
    total_incidents_7d: int
    high_risk_zones: int
    active_patterns: int
    pending_alerts: int
    risk_trend: str
    top_crime_types: list[dict]
    last_updated: datetime


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    version: str
    database: str
    ml_models: list[str]
    uptime_seconds: float
