# NYC Covid & Flu Tracker

Tracks and visualizes weekly COVID-19 and influenza cases in New York City, using public data from the [NYC DOHMH respiratory illness data repository](https://github.com/nychealth/respiratory-illness-data).

## Features

- Interactive Chart.js dashboard with toggleable COVID/flu lines, date-range picker, quick-range buttons, and monthly aggregation
- REST API (`GET /api/v1/cases`) with filtering by date range, disease type, and granularity
- Automated daily data ingestion via GitHub Actions (9 AM ET)
- Full pytest test suite (23 tests) covering parsing, upserts, and API endpoints
- Dockerized for easy deployment

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Initialise the database and fetch data

```bash
python -m ingestion.ingest
```

### 3. Start the server

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000](http://localhost:8000) for the dashboard, or [http://localhost:8000/docs](http://localhost:8000/docs) for the Swagger UI.

## API

### `GET /api/v1/cases`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start_date` | `YYYY-MM-DD` | — | Filter from date |
| `end_date` | `YYYY-MM-DD` | — | Filter to date |
| `disease_type` | `covid` / `flu` / `all` | `all` | Disease filter |
| `granularity` | `daily` / `weekly` / `monthly` | `weekly` | Time aggregation |

**Example:**

```bash
curl "http://localhost:8000/api/v1/cases?start_date=2024-01-01&granularity=monthly"
```

## Running tests

```bash
python -m pytest tests/ -v
```

## Docker

```bash
docker build -t nyc-tracker .
docker run -p 8000:8000 nyc-tracker
```

## Data sources

| File | Description |
|------|-------------|
| `Case_data_COVID-19.csv` | Weekly NYC COVID-19 case counts |
| `Case_data_influenza.csv` | Weekly NYC influenza case counts |

Data is updated weekly by NYC DOHMH. The ingestion script is idempotent — running it multiple times will not duplicate records.

## Project structure

```
├── app/
│   ├── main.py          # FastAPI app
│   ├── database.py      # SQLAlchemy engine & session
│   ├── models.py        # CaseRecord ORM model
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database queries & upserts
│   └── routers/
│       └── cases.py     # /api/v1/cases endpoint
├── ingestion/
│   └── ingest.py        # Data fetching & ingestion script
├── static/
│   └── index.html       # Chart.js dashboard
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_ingestion.py
├── .github/workflows/
│   ├── ci.yml           # Run tests on push/PR
│   └── ingest.yml       # Daily 9 AM ET data fetch
├── Dockerfile
└── requirements.txt
```
