"""Pattern detection engine for identifying crime patterns."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4
import numpy as np
from scipy import spatial
from sklearn.cluster import DBSCAN

from crime_radar.core.models import CrimeIncident, PatternDetection


class PatternDetector:
    """Detects patterns in crime data using clustering and temporal analysis."""

    def __init__(self, min_incidents: int = 3, spatial_threshold_km: float = 0.5):
        self.min_incidents = min_incidents
        self.spatial_threshold_km = spatial_threshold_km

    async def detect_patterns(
        self, incidents: list[CrimeIncident], days_lookback: int = 7
    ) -> list[PatternDetection]:
        """Detect all types of patterns in incident data."""
        patterns = []

        hotspot_patterns = await self._detect_hotspots(incidents)
        patterns.extend(hotspot_patterns)

        serial_patterns = await self._detect_serial_incidents(incidents)
        patterns.extend(serial_patterns)

        temporal_patterns = await self._detect_temporal_patterns(incidents)
        patterns.extend(temporal_patterns)

        return patterns

    async def _detect_hotspots(
        self, incidents: list[CrimeIncident]
    ) -> list[PatternDetection]:
        """Detect crime hotspots using density-based clustering."""
        if len(incidents) < self.min_incidents:
            return []

        coords = np.array([[i.coordinates[0], i.coordinates[1]] for i in incidents])

        kms_per_radian = 6371.0088
        epsilon = self.spatial_threshold_km / kms_per_radian

        clustering = DBSCAN(
            eps=epsilon, min_samples=self.min_incidents, metric="haversine"
        )
        labels = clustering.fit_predict(np.radians(coords))

        patterns = []
        unique_labels = set(labels) - {-1}

        for label in unique_labels:
            cluster_indices = np.where(labels == label)[0]
            cluster_incidents = [incidents[i] for i in cluster_indices]

            center = coords[cluster_indices].mean(axis=0)
            radius = coords[cluster_indices].std(axis=0).max() * 111  # km conversion

            pattern = PatternDetection(
                id=uuid4(),
                pattern_type="hotspot",
                confidence_score=self._calculate_hotspot_confidence(
                    len(cluster_incidents), radius
                ),
                description=f"Crime hotspot detected with {len(cluster_incidents)} incidents",
                involved_incidents=[i.id for i in cluster_incidents],
                geographic_radius_km=float(radius),
                detected_at=datetime.utcnow(),
            )
            patterns.append(pattern)

        return patterns

    async def _detect_serial_incidents(
        self, incidents: list[CrimeIncident]
    ) -> list[PatternDetection]:
        """Detect potential serial incidents (similar MO, close in time/space)."""
        patterns = []

        by_type = self._group_by_crime_type(incidents)

        for crime_type, type_incidents in by_type.items():
            sorted_incidents = sorted(type_incidents, key=lambda x: x.reported_at)

            for i in range(len(sorted_incidents) - self.min_incidents + 1):
                window = sorted_incidents[i : i + self.min_incidents]

                if self._is_serial(window):
                    temporal_span = (
                        window[-1].reported_at - window[0].reported_at
                    ).total_seconds() / 3600

                    pattern = PatternDetection(
                        id=uuid4(),
                        pattern_type="serial_incidents",
                        confidence_score=self._calculate_serial_confidence(window),
                        description=f"Potential serial {crime_type.value} - {len(window)} similar incidents",
                        involved_incidents=[j.id for j in window],
                        temporal_span_hours=float(temporal_span),
                        predicted_next_incident=self._predict_next_incident(window),
                        detected_at=datetime.utcnow(),
                    )
                    patterns.append(pattern)

        return patterns

    async def _detect_temporal_patterns(
        self, incidents: list[CrimeIncident]
    ) -> list[PatternDetection]:
        """Detect temporal patterns (time-of-day, day-of-week)."""
        patterns = []

        hourly_counts = [0] * 24
        for incident in incidents:
            hour = incident.reported_at.hour
            hourly_counts[hour] += 1

        peak_hours = [
            i for i, count in enumerate(hourly_counts) if count > np.mean(hourly_counts) * 2
        ]

        if peak_hours:
            pattern = PatternDetection(
                id=uuid4(),
                pattern_type="temporal",
                confidence_score=min(0.9, len(peak_hours) / 24),
                description=f"Peak crime hours detected: {peak_hours}",
                involved_incidents=[],
                detected_at=datetime.utcnow(),
            )
            patterns.append(pattern)

        return patterns

    def _group_by_crime_type(
        self, incidents: list[CrimeIncident]
    ) -> dict:
        """Group incidents by crime type."""
        groups = {}
        for incident in incidents:
            if incident.crime_type not in groups:
                groups[incident.crime_type] = []
            groups[incident.crime_type].append(incident)
        return groups

    def _is_serial(self, incidents: list[CrimeIncident]) -> bool:
        """Check if incidents form a potential serial pattern."""
        if len(incidents) < self.min_incidents:
            return False

        for i in range(1, len(incidents)):
            time_diff = abs(
                (incidents[i].reported_at - incidents[i - 1].reported_at).total_seconds()
            )
            if time_diff > 72 * 3600:
                return False

        coords = np.array([[i.coordinates[0], i.coordinates[1]] for i in incidents])
        if coords.shape[0] > 1:
            distances = spatial.distance.pdist(coords, metric="haversine") * 6371
            if distances.max() > 10:
                return False

        return True

    def _calculate_hotspot_confidence(
        self, incident_count: int, radius_km: float
    ) -> float:
        """Calculate confidence score for hotspot."""
        count_score = min(1.0, incident_count / 10)
        density_score = 1.0 / (1 + radius_km)
        return 0.5 * count_score + 0.5 * density_score

    def _calculate_serial_confidence(self, incidents: list[CrimeIncident]) -> float:
        """Calculate confidence score for serial incidents."""
        base_confidence = min(1.0, len(incidents) / 5)

        coords = np.array([[i.coordinates[0], i.coordinates[1]] for i in incidents])
        if coords.shape[0] > 1:
            compactness = 1.0 / (1 + spatial.distance.pdist(coords).mean())
        else:
            compactness = 1.0

        return 0.6 * base_confidence + 0.4 * compactness

    def _predict_next_incident(
        self, incidents: list[CrimeIncident]
    ) -> dict:
        """Predict where/when the next incident might occur."""
        if len(incidents) < 2:
            return {}

        avg_lat = np.mean([i.coordinates[0] for i in incidents])
        avg_lon = np.mean([i.coordinates[1] for i in incidents])

        time_diffs = [
            (incidents[i].reported_at - incidents[i - 1].reported_at).total_seconds()
            for i in range(1, len(incidents))
        ]
        avg_interval = np.mean(time_diffs)

        last_time = incidents[-1].reported_at
        predicted_time = last_time + timedelta(seconds=avg_interval)

        return {
            "predicted_location": {"latitude": avg_lat, "longitude": avg_lon},
            "predicted_time": predicted_time.isoformat(),
            "confidence": 0.5 + (len(incidents) * 0.1),
        }
