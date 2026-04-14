"""Risk prediction and zone scoring system."""

from datetime import datetime, timedelta
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

from crime_radar.core.models import Zone, RiskLevel, CrimeType, CrimeIncident


class RiskPredictor:
    """Predicts risk levels for geographic zones."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )
        self.scaler = StandardScaler()
        self.feature_columns = [
            "incident_count_24h",
            "incident_count_7d",
            "incident_count_30d",
            "hour_of_day",
            "day_of_week",
            "population_density",
            "time_since_last_incident",
        ]

    def calculate_risk_score(self, zone: Zone) -> tuple[float, RiskLevel]:
        """Calculate risk score for a zone (0-100)."""
        score = 0.0

        if zone.incident_count_24h > 0:
            score += min(30, zone.incident_count_24h * 5)

        if zone.incident_count_7d > 0:
            score += min(25, zone.incident_count_7d * 2)

        if zone.incident_count_30d > 0:
            score += min(20, zone.incident_count_30d)

        if zone.dominant_crime_types:
            crime_severity = sum(
                self._crime_type_weight(ct) for ct in zone.dominant_crime_types
            )
            score += min(15, crime_severity)

        if zone.trend_direction == "increasing":
            score += 10
        elif zone.trend_direction == "decreasing":
            score -= 5

        score = max(0, min(100, score))
        risk_level = self._score_to_level(score)

        return score, risk_level

    def _crime_type_weight(self, crime_type: CrimeType) -> float:
        """Get weight for crime type severity."""
        weights = {
            CrimeType.HOMICIDE: 5.0,
            CrimeType.ASSAULT: 4.0,
            CrimeType.ROBBERY: 4.0,
            CrimeType.BURGLARY: 3.0,
            CrimeType.THEFT: 2.0,
            CrimeType.VANDALISM: 1.5,
            CrimeType.DRUG_OFFENSE: 2.0,
            CrimeType.WEAPONS: 4.5,
            CrimeType.FRAUD: 1.0,
            CrimeType.OTHER: 1.0,
        }
        return weights.get(crime_type, 1.0)

    def _score_to_level(self, score: float) -> RiskLevel:
        """Convert numeric score to risk level."""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.ELEVATED
        elif score >= 25:
            return RiskLevel.MODERATE
        elif score >= 10:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE

    async def predict_future_risk(
        self,
        zone: Zone,
        hours_ahead: int = 24,
    ) -> dict:
        """Predict risk for a zone in the future."""
        features = self._extract_features(zone)
        features["hour_of_day"] = (datetime.utcnow().hour + hours_ahead) % 24

        X = self._prepare_features(features)
        X_scaled = self.scaler.fit_transform(X)

        predicted_score = self.model.predict(X_scaled)[0]
        predicted_score = max(0, min(100, predicted_score))

        return {
            "zone_id": str(zone.id),
            "hours_ahead": hours_ahead,
            "predicted_risk_score": float(predicted_score),
            "predicted_risk_level": self._score_to_level(predicted_score).value,
            "confidence": 0.75,
            "model_version": "1.0.0",
        }

    def _extract_features(self, zone: Zone) -> dict:
        """Extract features from zone for model input."""
        return {
            "incident_count_24h": zone.incident_count_24h,
            "incident_count_7d": zone.incident_count_7d,
            "incident_count_30d": zone.incident_count_30d,
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday(),
            "population_density": (
                zone.population / zone.area_sq_km if zone.area_sq_km > 0 else 0
            ),
            "time_since_last_incident": (
                (datetime.utcnow() - zone.last_updated).total_seconds() / 3600
                if zone.last_updated
                else 999
            ),
        }

    def _prepare_features(self, features: dict) -> np.ndarray:
        """Prepare feature array for model."""
        X = np.array([[features.get(col, 0) for col in self.feature_columns]])
        return X

    def train(self, historical_data: pd.DataFrame) -> dict:
        """Train the risk prediction model on historical data."""
        X = historical_data[self.feature_columns]
        y = historical_data["risk_score"]

        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)

        train_score = self.model.score(X_scaled, y)

        return {
            "model_version": "1.0.0",
            "training_samples": len(X),
            "r2_score": float(train_score),
            "feature_importance": dict(
                zip(self.feature_columns, self.model.feature_importances_.tolist())
            ),
        }
