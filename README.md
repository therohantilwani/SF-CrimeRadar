# SF-Crime radar

AI-Powered Security Intelligence Platform for law enforcement agencies.

## Quick Start

```bash
# Install dependencies
pip install -e .

# Start the API server
uvicorn crime_radar.api.routes:app --reload

# Open the dashboard
open crime_radar/dashboard/index.html
```

## Project Structure

```
crime_radar/
├── api/              # FastAPI routes and schemas
├── core/             # Core configuration and models
├── data/             # Data ingestion layer
├── ml/               # Machine learning modules
├── dashboard/        # Frontend dashboard UI
├── utils/            # Utility functions
└── tests/            # Test suite
```

## API Endpoints

- `GET /api/v1/dashboard` - Dashboard summary
- `GET /api/v1/incidents` - List incidents
- `GET /api/v1/zones/risk` - Zone risk assessments
- `GET /api/v1/patterns` - Detected patterns
- `GET /api/v1/alerts` - Security alerts
- `GET /api/v1/predictions/{zone_id}` - Risk predictions

See SPEC.md for full documentation.
