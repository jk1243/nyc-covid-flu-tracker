"""Unit tests for the CSV parsing and upsert logic."""

import textwrap
from datetime import date
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from app.crud import upsert_record
from ingestion.ingest import fetch_csv, parse_covid, parse_flu, run_ingestion


# ── parse_covid ───────────────────────────────────────────────────────────────

def test_parse_covid_happy_path():
    raw = textwrap.dedent("""\
        date,COVID-19 cases overall
        2024-01-06,1500
        2024-01-13,1200
    """)
    df = parse_covid(pd.read_csv(StringIO(raw)))
    assert list(df.columns) == ["date", "covid_cases"]
    assert len(df) == 2
    assert df.iloc[0]["covid_cases"] == 1500
    assert df.iloc[0]["date"] == date(2024, 1, 6)


def test_parse_covid_skips_invalid_dates():
    raw = textwrap.dedent("""\
        date,COVID-19 cases overall
        not-a-date,999
        2024-01-13,1200
    """)
    df = parse_covid(pd.read_csv(StringIO(raw)))
    assert len(df) == 1
    assert df.iloc[0]["date"] == date(2024, 1, 13)


def test_parse_covid_wrong_columns_raises():
    raw = "week,cases\n2024-01-06,100\n"
    with pytest.raises(ValueError, match="Unexpected COVID CSV columns"):
        parse_covid(pd.read_csv(StringIO(raw)))


# ── parse_flu ─────────────────────────────────────────────────────────────────

def test_parse_flu_happy_path():
    raw = textwrap.dedent("""\
        date,Influenza cases overall
        2024-01-06,300
        2024-01-13,450
    """)
    df = parse_flu(pd.read_csv(StringIO(raw)))
    assert list(df.columns) == ["date", "flu_cases"]
    assert df.iloc[1]["flu_cases"] == 450


def test_parse_flu_wrong_columns_raises():
    raw = "week,flu\n2024-01-06,100\n"
    with pytest.raises(ValueError, match="Unexpected flu CSV columns"):
        parse_flu(pd.read_csv(StringIO(raw)))


# ── fetch_csv ─────────────────────────────────────────────────────────────────

def test_fetch_csv_timeout_raises():
    with patch("ingestion.ingest.requests.get", side_effect=requests.exceptions.Timeout):
        with pytest.raises(requests.exceptions.Timeout):
            fetch_csv("http://example.com/data.csv")


def test_fetch_csv_http_error_raises():
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
    with patch("ingestion.ingest.requests.get", return_value=mock_response):
        with pytest.raises(requests.exceptions.HTTPError):
            fetch_csv("http://example.com/data.csv")


# ── upsert_record (via db fixture) ────────────────────────────────────────────

def test_upsert_inserts_new_record(db):
    rec = upsert_record(db, date=date(2024, 1, 6), covid_cases=100, flu_cases=50)
    assert rec.covid_cases == 100
    assert rec.flu_cases == 50


def test_upsert_updates_existing_record(db):
    upsert_record(db, date=date(2024, 1, 6), covid_cases=100, flu_cases=50)
    rec = upsert_record(db, date=date(2024, 1, 6), covid_cases=200, flu_cases=None)
    assert rec.covid_cases == 200
    assert rec.flu_cases == 50  # unchanged when None passed


def test_upsert_does_not_duplicate(db):
    from app.models import CaseRecord
    upsert_record(db, date=date(2024, 1, 6), covid_cases=100, flu_cases=50)
    upsert_record(db, date=date(2024, 1, 6), covid_cases=200, flu_cases=60)
    count = db.query(CaseRecord).count()
    assert count == 1


# ── run_ingestion (mocked network) ────────────────────────────────────────────

COVID_CSV = textwrap.dedent("""\
    date,COVID-19 cases overall
    2024-01-06,1500
    2024-01-13,1200
""")

FLU_CSV = textwrap.dedent("""\
    date,Influenza cases overall
    2024-01-06,300
    2024-01-13,450
""")


def _make_response(text):
    mock = MagicMock()
    mock.text = text
    mock.raise_for_status = MagicMock()
    return mock


def test_run_ingestion_returns_row_count(db):
    with patch("ingestion.ingest.requests.get") as mock_get:
        mock_get.side_effect = [_make_response(COVID_CSV), _make_response(FLU_CSV)]
        with patch("ingestion.ingest.SessionLocal", return_value=db):
            with patch("ingestion.ingest.init_db"):
                count = run_ingestion()
    assert count == 2
