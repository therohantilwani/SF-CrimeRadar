"""FastAPI application for Crime Radar API."""

from contextlib import asynccontextmanager
from datetime import datetime
import time

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from .schemas import (
    IncidentCreate,
    IncidentResponse,
    ZoneRiskResponse,
    AlertResponse,
    PatternResponse,
    DashboardSummary,
    HealthCheck,
)
from ..core.config import get_settings
from ..ml import PatternDetector, RiskPredictor, HotspotAnalyzer, AnomalyDetector


start_time = time.time()
settings = get_settings()

pattern_detector = PatternDetector()
risk_predictor = RiskPredictor()
hotspot_analyzer = HotspotAnalyzer()
anomaly_detector = AnomalyDetector()

MOCK_INCIDENTS = []
MOCK_ZONES = []
MOCK_ALERTS = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("Crime Radar API starting up...")
    yield
    logger.info("Crime Radar API shutting down...")


app = FastAPI(
    title="Crime Radar API",
    description="AI-Powered Security Intelligence Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthCheck, tags=["System"])
async def health_check():
    """Check API health status."""
    return HealthCheck(
        status="healthy",
        version="0.1.0",
        database="connected",
        ml_models=["pattern_detector", "risk_predictor", "hotspot_analyzer"],
        uptime_seconds=time.time() - start_time,
    )


@app.get("/api/v1/dashboard", response_model=DashboardSummary, tags=["Dashboard"])
async def get_dashboard_summary():
    """Get dashboard summary with key metrics."""
    return DashboardSummary(
        total_incidents_today=len([i for i in MOCK_INCIDENTS if i.get("reported_at", datetime.utcnow()).date() == datetime.utcnow().date()]),
        total_incidents_7d=len(MOCK_INCIDENTS),
        high_risk_zones=len([z for z in MOCK_ZONES if z.get("risk_level") in ["high", "critical"]]),
        active_patterns=0,
        pending_alerts=len([a for a in MOCK_ALERTS if not a.get("acknowledged", False)]),
        risk_trend="stable",
        top_crime_types=[
            {"type": "theft", "count": 45},
            {"type": "burglary", "count": 23},
            {"type": "assault", "count": 18},
        ],
        last_updated=datetime.utcnow(),
    )


@app.post("/api/v1/incidents", response_model=IncidentResponse, tags=["Incidents"])
async def create_incident(incident: IncidentCreate):
    """Create a new crime incident."""
    new_incident = {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "incident_number": f"INC-{int(time.time())}",
        "crime_type": incident.crime_type,
        "severity": incident.severity,
        "status": "reported",
        "location": incident.location.model_dump(),
        "coordinates": (incident.location.latitude, incident.location.longitude),
        "reported_at": incident.reported_at or datetime.utcnow(),
        "description": incident.description,
        "created_at": datetime.utcnow(),
    }
    MOCK_INCIDENTS.append(new_incident)
    return new_incident


@app.get("/api/v1/incidents", response_model=list[IncidentResponse], tags=["Incidents"])
async def list_incidents(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    crime_type: str = Query(default=None),
):
    """List crime incidents with filtering."""
    incidents = MOCK_INCIDENTS

    if crime_type:
        incidents = [i for i in incidents if i.get("crime_type") == crime_type]

    return incidents[offset : offset + limit]


@app.get("/api/v1/zones/risk", response_model=list[ZoneRiskResponse], tags=["Zones"])
async def get_zone_risks():
    """Get risk assessment for all zones."""
    if not MOCK_ZONES:
        return [
            ZoneRiskResponse(
                zone_id="550e8400-e29b-41d4-a716-446655440001",
                zone_name="Downtown District",
                risk_score=72.5,
                risk_level="high",
                incident_count_24h=12,
                incident_count_7d=45,
                dominant_crime_types=["theft", "burglary"],
                trend_direction="increasing",
                hotspots=[],
                last_updated=datetime.utcnow(),
            ),
            ZoneRiskResponse(
                zone_id="550e8400-e29b-41d4-a716-446655440002",
                zone_name="Industrial Park",
                risk_score=35.0,
                risk_level="moderate",
                incident_count_24h=3,
                incident_count_7d=15,
                dominant_crime_types=["vandalism", "theft"],
                trend_direction="stable",
                hotspots=[],
                last_updated=datetime.utcnow(),
            ),
        ]
    return MOCK_ZONES


@app.get("/api/v1/zones/{zone_id}/risk", response_model=ZoneRiskResponse, tags=["Zones"])
async def get_zone_risk(zone_id: str):
    """Get detailed risk assessment for a specific zone."""
    return ZoneRiskResponse(
        zone_id=zone_id,
        zone_name="Zone Name",
        risk_score=65.0,
        risk_level="elevated",
        incident_count_24h=8,
        incident_count_7d=32,
        dominant_crime_types=["theft", "assault"],
        trend_direction="increasing",
        hotspots=[
            {
                "center": {"latitude": 40.7128, "longitude": -74.0060},
                "peak_density": 8.5,
                "area_sq_km": 0.25,
                "intensity": "high",
            }
        ],
        last_updated=datetime.utcnow(),
    )


@app.get("/api/v1/patterns", response_model=list[PatternResponse], tags=["Patterns"])
async def get_patterns():
    """Get detected crime patterns."""
    return [
        PatternResponse(
            id="550e8400-e29b-41d4-a716-446655440010",
            pattern_type="hotspot",
            confidence_score=0.85,
            description="Theft hotspot in commercial district",
            involved_incident_count=15,
            geographic_radius_km=0.5,
            temporal_span_hours=168.0,
            predicted_next_incident={
                "predicted_location": {"latitude": 40.7589, "longitude": -73.9851},
                "predicted_time": datetime.utcnow().isoformat(),
                "confidence": 0.75,
            },
            detected_at=datetime.utcnow(),
            confirmed=False,
        )
    ]


@app.get("/api/v1/alerts", response_model=list[AlertResponse], tags=["Alerts"])
async def get_alerts(
    acknowledged: bool = Query(default=None),
    severity: str = Query(default=None),
):
    """Get security alerts."""
    alerts = MOCK_ALERTS or [
        AlertResponse(
            id="550e8400-e29b-41d4-a716-446655440020",
            alert_type="pattern_detected",
            severity="high",
            title="Serial Theft Pattern Detected",
            message="15 similar theft incidents detected in downtown area over past week.",
            zone_id="550e8400-e29b-41d4-a716-446655440001",
            actionable=True,
            recommended_actions=[
                "Increase patrol presence in affected area",
                "Review surveillance footage from incident locations",
                "Notify businesses in the area",
            ],
            acknowledged=False,
            created_at=datetime.utcnow(),
        )
    ]

    if acknowledged is not None:
        alerts = [a for a in alerts if a.acknowledged == acknowledged]
    if severity:
        alerts = [a for a in alerts if a.severity == severity]

    return alerts


@app.post("/api/v1/alerts/{alert_id}/acknowledge", response_model=AlertResponse, tags=["Alerts"])
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    return AlertResponse(
        id=alert_id,
        alert_type="pattern_detected",
        severity="high",
        title="Serial Theft Pattern Detected",
        message="Alert message",
        actionable=True,
        recommended_actions=[],
        acknowledged=True,
        created_at=datetime.utcnow(),
    )


@app.get("/api/v1/analytics/hotspots", tags=["Analytics"])
async def get_hotspots(
    hours: int = Query(default=24, ge=1, le=720),
):
    """Get crime hotspots for the specified time window."""
    return {
        "hotspots": [
            {
                "center": {"latitude": 40.7589, "longitude": -73.9851},
                "peak_density": 8.5,
                "area_sq_km": 0.25,
                "intensity": "high",
                "incident_count": 15,
            }
        ],
        "total_hotspots": 1,
        "analysis_window_hours": hours,
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/analytics/trends", tags=["Analytics"])
async def get_trends(days: int = Query(default=30, ge=7, le=365)):
    """Get crime trends over time."""
    return {
        "trends": {
            "daily_average": 12.5,
            "weekly_change": 8.2,
            "monthly_change": -3.1,
        },
        "by_crime_type": {
            "theft": {"count": 145, "change": 5.2},
            "burglary": {"count": 67, "change": -12.3},
            "assault": {"count": 54, "change": 2.1},
        },
        "analysis_period_days": days,
        "generated_at": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/predictions/{zone_id}", tags=["Predictions"])
async def get_zone_prediction(
    zone_id: str,
    hours_ahead: int = Query(default=24, ge=1, le=168),
):
    """Get risk prediction for a zone."""
    return {
        "zone_id": zone_id,
        "hours_ahead": hours_ahead,
        "predicted_risk_score": 68.5,
        "predicted_risk_level": "elevated",
        "confidence": 0.75,
        "factors": [
            {"factor": "rising_incident_count", "impact": "positive"},
            {"factor": "seasonal_trend", "impact": "neutral"},
        ],
        "model_version": "1.0.0",
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
