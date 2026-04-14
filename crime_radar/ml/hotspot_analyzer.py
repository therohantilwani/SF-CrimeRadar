"""Hotspot analysis for crime density mapping."""

from datetime import datetime, timedelta
from typing import Optional
import numpy as np
from scipy.stats import gaussian_kde
from sklearn.cluster import MeanShift

from crime_radar.core.models import CrimeIncident, Zone, RiskLevel


class HotspotAnalyzer:
    """Analyzes crime hotspots using spatial statistics."""

    def __init__(self, bandwidth_km: float = 0.5):
        self.bandwidth_km = bandwidth_km

    async def identify_hotspots(
        self,
        incidents: list[CrimeIncident],
        min_density: float = 2.0,
    ) -> list[dict]:
        """Identify crime hotspots from incidents."""
        if len(incidents) < 5:
            return []

        coords = np.array([[i.coordinates[0], i.coordinates[1]] for i in incidents])
        weights = np.array([self._severity_weight(i.severity) for i in incidents])

        try:
            kde = gaussian_kde(coords.T, weights=weights, bw_method=0.1)
        except Exception:
            return []

        grid_resolution = 50
        lat_min, lat_max = coords[:, 0].min(), coords[:, 0].max()
        lon_min, lon_max = coords[:, 1].min(), coords[:, 1].max()

        lat_grid = np.linspace(lat_min, lat_max, grid_resolution)
        lon_grid = np.linspace(lon_min, lon_max, grid_resolution)
        lon_mesh, lat_mesh = np.meshgrid(lon_grid, lat_grid)

        positions = np.vstack([lat_mesh.ravel(), lon_mesh.ravel()])
        density = kde(positions).reshape(lat_mesh.shape)

        hotspots = self._extract_hotspots(
            lat_mesh, lon_mesh, density, min_density
        )

        return hotspots

    def _severity_weight(self, severity: str) -> float:
        """Weight incidents by severity."""
        weights = {
            "critical": 3.0,
            "high": 2.5,
            "medium": 1.5,
            "low": 1.0,
        }
        return weights.get(severity.lower(), 1.0)

    def _extract_hotspots(
        self,
        lat_grid: np.ndarray,
        lon_grid: np.ndarray,
        density: np.ndarray,
        min_density: float,
    ) -> list[dict]:
        """Extract hotspot regions from density grid."""
        hotspots = []

        threshold = np.percentile(density[density > 0], 75)
        mask = density > max(threshold, min_density)

        labeled, num_features = self._label_regions(mask)

        for region_id in range(1, num_features + 1):
            region_mask = labeled == region_id
            region_density = np.where(region_mask, density, 0)
            peak_idx = np.unravel_index(region_density.argmax(), region_density.shape)

            hotspots.append({
                "center": {
                    "latitude": float(lat_grid[peak_idx]),
                    "longitude": float(lon_grid[peak_idx]),
                },
                "peak_density": float(density[peak_idx]),
                "area_sq_km": float(region_mask.sum() * self._cell_area()),
                "intensity": self._classify_intensity(density[peak_idx]),
            })

        hotspots.sort(key=lambda x: x["peak_density"], reverse=True)
        return hotspots

    def _label_regions(self, mask: np.ndarray) -> tuple:
        """Simple region labeling for hotspot extraction."""
        labeled = np.zeros_like(mask, dtype=int)
        current_label = 0

        for i in range(mask.shape[0]):
            for j in range(mask.shape[1]):
                if mask[i, j] and labeled[i, j] == 0:
                    current_label += 1
                    self._flood_fill(mask, labeled, i, j, current_label)

        return labeled, current_label

    def _flood_fill(
        self, mask: np.ndarray, labeled: np.ndarray, i: int, j: int, label: int
    ) -> None:
        """Flood fill to label connected regions."""
        if i < 0 or i >= mask.shape[0] or j < 0 or j >= mask.shape[1]:
            return
        if not mask[i, j] or labeled[i, j] != 0:
            return

        labeled[i, j] = label
        stack = [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
        for ni, nj in stack:
            self._flood_fill(mask, labeled, ni, nj, label)

    def _cell_area(self) -> float:
        """Estimate area of one grid cell in km²."""
        lat_step = 0.001
        lon_step = 0.001
        return lat_step * lon_step * 111 * 111

    def _classify_intensity(self, density: float) -> str:
        """Classify hotspot intensity."""
        if density > 10:
            return "critical"
        elif density > 5:
            return "high"
        elif density > 2:
            return "moderate"
        return "low"

    async def analyze_trends(
        self,
        incidents: list[CrimeIncident],
        zone: Zone,
        hours: int = 168,
    ) -> dict:
        """Analyze hotspot trends over time."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent = [i for i in incidents if i.reported_at > cutoff]

        current_hotspots = await self.identify_hotspots(incidents)

        older_cutoff = datetime.utcnow() - timedelta(hours=hours * 2)
        older = [i for i in incidents if older_cutoff < i.reported_at <= cutoff]
        older_hotspots = await self.identify_hotspots(older) if older else []

        trend = self._compare_hotspots(current_hotspots, older_hotspots)

        return {
            "zone_id": str(zone.id),
            "current_hotspots": len(current_hotspots),
            "previous_hotspots": len(older_hotspots),
            "trend": trend,
            "analysis_window_hours": hours,
            "analyzed_at": datetime.utcnow().isoformat(),
        }

    def _compare_hotspots(
        self, current: list[dict], previous: list[dict]
    ) -> str:
        """Compare current and previous hotspots to determine trend."""
        if len(current) > len(previous) * 1.2:
            return "increasing"
        elif len(current) < len(previous) * 0.8:
            return "decreasing"
        return "stable"
