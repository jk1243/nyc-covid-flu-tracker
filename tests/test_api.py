"""Integration tests for the /api/v1/cases endpoint."""

from datetime import date

from app.crud import upsert_record


def _seed(db):
    """Insert a handful of known records spanning two months."""
    upsert_record(db, date=date(2024, 1, 6),  covid_cases=1500, flu_cases=300)
    upsert_record(db, date=date(2024, 1, 13), covid_cases=1200, flu_cases=450)
    upsert_record(db, date=date(2024, 1, 20), covid_cases=900,  flu_cases=500)
    upsert_record(db, date=date(2024, 2, 3),  covid_cases=800,  flu_cases=600)
    upsert_record(db, date=date(2024, 2, 10), covid_cases=750,  flu_cases=650)


# ── Basic retrieval ───────────────────────────────────────────────────────────

def test_get_cases_returns_all(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases")
    assert resp.status_code == 200
    assert len(resp.json()) == 5


def test_get_cases_start_date_filter(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?start_date=2024-02-01")
    data = resp.json()
    assert all(r["date"] >= "2024-02-01" for r in data)
    assert len(data) == 2


def test_get_cases_end_date_filter(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?end_date=2024-01-13")
    data = resp.json()
    assert all(r["date"] <= "2024-01-13" for r in data)
    assert len(data) == 2


def test_get_cases_date_range(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?start_date=2024-01-13&end_date=2024-01-20")
    data = resp.json()
    assert len(data) == 2


# ── disease_type filter ───────────────────────────────────────────────────────

def test_disease_type_covid(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?disease_type=covid")
    data = resp.json()
    assert all(r["flu_cases"] is None for r in data)
    assert any(r["covid_cases"] is not None for r in data)


def test_disease_type_flu(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?disease_type=flu")
    data = resp.json()
    assert all(r["covid_cases"] is None for r in data)
    assert any(r["flu_cases"] is not None for r in data)


def test_disease_type_all(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?disease_type=all")
    data = resp.json()
    assert any(r["covid_cases"] is not None for r in data)
    assert any(r["flu_cases"] is not None for r in data)


# ── granularity ───────────────────────────────────────────────────────────────

def test_granularity_weekly_returns_raw_rows(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?granularity=weekly")
    assert len(resp.json()) == 5


def test_granularity_monthly_aggregates(client, db):
    _seed(db)
    resp = client.get("/api/v1/cases?granularity=monthly")
    data = resp.json()
    # Two distinct months in seed data
    assert len(data) == 2
    jan = next(r for r in data if r["date"].startswith("2024-01"))
    feb = next(r for r in data if r["date"].startswith("2024-02"))
    assert jan["covid_cases"] == 1500 + 1200 + 900
    assert feb["flu_cases"]   == 600 + 650


# ── Edge cases ────────────────────────────────────────────────────────────────

def test_empty_db_returns_empty_list(client, db):
    resp = client.get("/api/v1/cases")
    assert resp.status_code == 200
    assert resp.json() == []


def test_invalid_disease_type_returns_422(client, db):
    resp = client.get("/api/v1/cases?disease_type=ebola")
    assert resp.status_code == 422


def test_invalid_granularity_returns_422(client, db):
    resp = client.get("/api/v1/cases?granularity=hourly")
    assert resp.status_code == 422
