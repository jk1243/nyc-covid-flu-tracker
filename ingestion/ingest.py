"""
Data ingestion script.

Fetches the latest weekly COVID-19 and influenza case CSV files from the
NYC DOHMH respiratory illness data repository and upserts them into the
local SQLite database.

Usage:
    python -m ingestion.ingest
"""

import logging
import sys
from io import StringIO

import pandas as pd
import requests

# Allow running from the project root as `python -m ingestion.ingest`
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.crud import upsert_record

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

BASE_URL = "https://raw.githubusercontent.com/nychealth/respiratory-illness-data/main/data"
COVID_CSV_URL = f"{BASE_URL}/Case_data_COVID-19.csv"
FLU_CSV_URL = f"{BASE_URL}/Case_data_influenza.csv"

REQUEST_TIMEOUT = 30  # seconds


def fetch_csv(url: str) -> pd.DataFrame:
    """Download a CSV from *url* and return it as a DataFrame."""
    logger.info("Fetching %s", url)
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        logger.error("Request timed out for %s", url)
        raise
    except requests.exceptions.HTTPError as exc:
        logger.error("HTTP error fetching %s: %s", url, exc)
        raise
    except requests.exceptions.RequestException as exc:
        logger.error("Network error fetching %s: %s", url, exc)
        raise

    return pd.read_csv(StringIO(response.text))


def parse_covid(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise the COVID-19 DataFrame to columns: date, covid_cases."""
    expected_col = "COVID-19 cases overall"
    if expected_col not in df.columns:
        raise ValueError(f"Unexpected COVID CSV columns: {list(df.columns)}")

    df = df.rename(columns={"date": "date", expected_col: "covid_cases"})
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce").dt.date
    df["covid_cases"] = pd.to_numeric(df["covid_cases"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["date"])
    return df[["date", "covid_cases"]]


def parse_flu(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise the influenza DataFrame to columns: date, flu_cases."""
    expected_col = "Influenza cases overall"
    if expected_col not in df.columns:
        raise ValueError(f"Unexpected flu CSV columns: {list(df.columns)}")

    df = df.rename(columns={"date": "date", expected_col: "flu_cases"})
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce").dt.date
    df["flu_cases"] = pd.to_numeric(df["flu_cases"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["date"])
    return df[["date", "flu_cases"]]


def run_ingestion() -> int:
    """Fetch, parse, and upsert all records. Returns the number of rows processed."""
    covid_df = parse_covid(fetch_csv(COVID_CSV_URL))
    flu_df = parse_flu(fetch_csv(FLU_CSV_URL))

    # Outer-join so a date missing from one source still gets stored
    merged = pd.merge(covid_df, flu_df, on="date", how="outer").sort_values("date")

    init_db()
    db = SessionLocal()
    try:
        count = 0
        for row in merged.itertuples(index=False):
            covid_val = None if pd.isna(row.covid_cases) else int(row.covid_cases)
            flu_val = None if pd.isna(row.flu_cases) else int(row.flu_cases)
            upsert_record(db, date=row.date, covid_cases=covid_val, flu_cases=flu_val)
            count += 1
        logger.info("Upserted %d records.", count)
        return count
    finally:
        db.close()


if __name__ == "__main__":
    try:
        run_ingestion()
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        sys.exit(1)
