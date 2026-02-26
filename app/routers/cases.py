from datetime import date as Date
from enum import Enum
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.crud import get_cases
from app.database import get_db
from app.schemas import CaseRecordOut

router = APIRouter(prefix="/api/v1", tags=["cases"])


class DiseaseType(str, Enum):
    covid = "covid"
    flu = "flu"
    all = "all"


class Granularity(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


def _aggregate(records: list[CaseRecordOut], granularity: Granularity) -> list[dict]:
    """
    Group records by the requested time bucket.

    The source data is already weekly, so 'daily' and 'weekly' both return
    the raw rows (one per reporting week).  'monthly' sums cases within each
    calendar month and labels the period with the first day of that month.
    """
    if granularity in (Granularity.daily, Granularity.weekly):
        return [r.model_dump() for r in records]

    # monthly aggregation
    buckets: dict[str, dict] = {}
    for r in records:
        key = r.date.strftime("%Y-%m-01")
        if key not in buckets:
            buckets[key] = {"date": key, "covid_cases": 0, "flu_cases": 0}
        if r.covid_cases is not None:
            buckets[key]["covid_cases"] += r.covid_cases
        if r.flu_cases is not None:
            buckets[key]["flu_cases"] += r.flu_cases

    return list(buckets.values())


@router.get("/cases", response_model=list[dict])
def read_cases(
    start_date: Optional[Date] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    end_date: Optional[Date] = Query(None, description="Filter up to date (YYYY-MM-DD)"),
    disease_type: DiseaseType = Query(DiseaseType.all, description="Disease to include"),
    granularity: Granularity = Query(Granularity.weekly, description="Time aggregation"),
    db: Session = Depends(get_db),
):
    rows = get_cases(db, start_date=start_date, end_date=end_date)
    records = [CaseRecordOut.model_validate(r) for r in rows]

    # Apply disease filter
    if disease_type == DiseaseType.covid:
        for r in records:
            r.flu_cases = None
    elif disease_type == DiseaseType.flu:
        for r in records:
            r.covid_cases = None

    return _aggregate(records, granularity)
