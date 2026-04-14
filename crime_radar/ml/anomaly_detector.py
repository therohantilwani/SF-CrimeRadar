"""Anomaly detection for unusual crime patterns."""

from datetime import datetime, timedelta
from typing import Optional
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from crime_radar.core.models import CrimeIncident


class AnomalyDetector:
    """Detects anomalous crime patterns that deviate from normal."""

    def __init__(self, contamination: float = 0.05):
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        self.scaler = StandardScaler()
        self.baseline_stats: Optional[dict] = None

    def detect_anomalies(
        self, incidents: list[CrimeIncident]
    ) -> list[dict]:
        """Detect anomalous incidents."""
        if len(incidents) < 10:
            return []

        features = self._extract_features(incidents)
        X = self.scaler.fit_transform(features)

        anomaly_labels = self.model.fit_predict(X)
        anomaly_scores = self.model.score_samples(X)

        anomalies = []
        for i, (label, score) in enumerate(zip(anomaly_labels, anomaly_scores)):
            if label == -1:
                anomalies.append({
                    "incident": incidents[i].model_dump(),
                    "anomaly_score": float(-score),
                    "anomaly_type": self._classify_anomaly(incidents[i], features[i]),
                    "confidence": float(1 - self.contamination),
                })

        anomalies.sort(key=lambda x: x["anomaly_score"], reverse=True)
        return anomalies

    def _extract_features(self, incidents: list[CrimeIncident]) -> np.ndarray:
        """Extract features for anomaly detection."""
        features = []

        for incident in incidents:
            lat, lon = incident.coordinates
            hour = incident.reported_at.hour
            day = incident.reported_at.weekday()

            severity_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
            severity = severity_map.get(incident.severity.lower(), 1)

            features.append([
                lat,
                lon,
                hour,
                day,
                severity,
                incident.weapons_involved,
                incident.injuries_reported,
            ])

        return np.array(features)

    def _classify_anomaly(self, incident: CrimeIncident, features: np.ndarray) -> str:
        """Classify the type of anomaly."""
        lat, lon, hour, day, severity, weapons, injuries = features

        if weapons or injuries:
            return "violent_incident"

        if hour < 6 or hour > 22:
            return "unusual_time"

        if severity >= 3:
            return "high_severity_anomaly"

        return "spatial_anomaly"

    async def detect_spatial_anomalies(
        self, incidents: list[CrimeIncident], zone_radius_km: float = 1.0
    ) -> list[dict]:
        """Detect spatial anomalies in crime distribution."""
        if len(incidents) < 10:
            return []

        coords = np.array([[i.coordinates[0], i.coordinates[1]] for i in incidents])
        center = coords.mean(axis=0)

        distances = np.sqrt(np.sum((coords - center) ** 2, axis=1))
        mean_dist = distances.mean()
        std_dist = distances.std()

        threshold = mean_dist + 2 * std_dist

        anomalies = []
        for i, (incident, dist) in enumerate(zip(incidents, distances)):
            if dist > threshold:
                anomalies.append({
                    "incident": incident.model_dump(),
                    "distance_from_center_km": float(dist * 111),
                    "deviation_from_mean": float((dist - mean_dist) / std_dist if std_dist > 0 else 0),
                })

        return anomalies

    async def detect_temporal_anomalies(
        self, incidents: list[CrimeIncident], lookback_days: int = 30
    ) -> list[dict]:
        """Detect temporal anomalies (unusual spikes or lulls)."""
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        recent = [i for i in incidents if i.reported_at > cutoff]

        if not recent:
            return []

        daily_counts = {}
        for incident in recent:
            date = incident.reported_at.date()
            daily_counts[date] = daily_counts.get(date, 0) + 1

        counts = np.array(list(daily_counts.values()))
        mean = counts.mean()
        std = counts.std() if len(counts) > 1 else 1

        threshold_high = mean + 2 * std
        threshold_low = max(0, mean - 2 * std)

        anomalies = []
        for date, count in daily_counts.items():
            if count > threshold_high:
                anomalies.append({
                    "date": str(date),
                    "incident_count": count,
                    "expected_range": f"{max(0, mean - 2*std):.0f}-{mean + 2*std:.0f}",
                    "anomaly_type": "spike",
                    "deviation": f"+{(count - mean) / std:.1f} std",
                })
            elif count < threshold_low:
                anomalies.append({
                    "date": str(date),
                    "incident_count": count,
                    "expected_range": f"{max(0, mean - 2*std):.0f}-{mean + 2*std:.0f}",
                    "anomaly_type": "lull",
                    "deviation": f"-{(mean - count) / std:.1f} std",
                })

        return anomalies

    def update_baseline(self, incidents: list[CrimeIncident]) -> dict:
        """Update baseline statistics for anomaly detection."""
        if not incidents:
            return {}

        features = self._extract_features(incidents)

        self.baseline_stats = {
            "mean_location": features[:, :2].mean(axis=0).tolist(),
            "std_location": features[:, :2].std(axis=0).tolist(),
            "hour_distribution": self._get_distribution(features[:, 2]),
            "day_distribution": self._get_distribution(features[:, 3]),
            "total_incidents": len(incidents),
            "updated_at": datetime.utcnow().isoformat(),
        }

        return self.baseline_stats

    def _get_distribution(self, values: np.ndarray) -> dict:
        """Get distribution statistics."""
        return {
            "mean": float(values.mean()),
            "std": float(values.std()),
            "min": float(values.min()),
            "max": float(values.max()),
        }
