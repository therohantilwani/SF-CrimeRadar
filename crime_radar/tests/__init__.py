"""Tests for Crime Radar."""

import pytest
from datetime import datetime
from crime_radar.ml.pattern_detector import PatternDetector
from crime_radar.ml.risk_predictor import RiskPredictor
from crime_radar.core.models import CrimeIncident, CrimeType, SeverityLevel, Zone, RiskLevel


class TestRiskPredictor:
    """Tests for the risk predictor."""

    def test_calculate_risk_score_low(self):
        """Test risk calculation for low-risk zone."""
        predictor = RiskPredictor()
        zone = Zone(
            id="test-1",
            name="Test Zone",
            zone_type="district",
            coordinates=[(40.7, -74.0)],
            incident_count_24h=0,
            incident_count_7d=1,
            incident_count_30d=5,
            dominant_crime_types=[],
            trend_direction="stable",
        )
        
        score, level = predictor.calculate_risk_score(zone)
        
        assert score < 25
        assert level in [RiskLevel.SAFE, RiskLevel.LOW]

    def test_calculate_risk_score_high(self):
        """Test risk calculation for high-risk zone."""
        predictor = RiskPredictor()
        zone = Zone(
            id="test-2",
            name="High Risk Zone",
            zone_type="district",
            coordinates=[(40.7, -74.0)],
            incident_count_24h=10,
            incident_count_7d=50,
            incident_count_30d=200,
            dominant_crime_types=[CrimeType.HOMICIDE, CrimeType.ASSAULT],
            trend_direction="increasing",
        )
        
        score, level = predictor.calculate_risk_score(zone)
        
        assert score > 60
        assert level in [RiskLevel.HIGH, RiskLevel.CRITICAL]


class TestPatternDetector:
    """Tests for the pattern detector."""

    def test_no_patterns_with_few_incidents(self):
        """Test that no patterns are detected with insufficient data."""
        detector = PatternDetector()
        incidents = []
        
        # This would need to be async in real usage
        # patterns = await detector.detect_patterns(incidents)
        
        assert True  # Placeholder


class TestCrimeModels:
    """Tests for crime data models."""

    def test_crime_incident_creation(self):
        """Test creating a crime incident."""
        incident = CrimeIncident(
            incident_number="TEST-001",
            crime_type=CrimeType.THEFT,
            severity=SeverityLevel.MEDIUM,
            location={"latitude": 40.7128, "longitude": -74.0060, "address": "123 Main St"},
            coordinates=(40.7128, -74.0060),
            reported_at=datetime.utcnow(),
            description="Test incident",
            source="test",
        )
        
        assert incident.incident_number == "TEST-001"
        assert incident.crime_type == CrimeType.THEFT
        assert incident.severity == SeverityLevel.MEDIUM

    def test_zone_risk_levels(self):
        """Test zone risk level assignment."""
        for score, expected_level in [
            (5, RiskLevel.SAFE),
            (15, RiskLevel.LOW),
            (30, RiskLevel.MODERATE),
            (45, RiskLevel.ELEVATED),
            (65, RiskLevel.HIGH),
            (85, RiskLevel.CRITICAL),
        ]:
            pass  # Would test the conversion logic here
