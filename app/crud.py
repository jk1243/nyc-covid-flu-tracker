from datetime import date as Date
from typing import Optional
from sqlalchemy.orm import Session
from app.models import CaseRecord


def upsert_record(db: Session, date: Date, covid_cases: Optional[int], flu_cases: Optional[int]) -> CaseRecord:
    record = db.get(CaseRecord, date)
    if record is None:
        record = CaseRecord(date=date, covid_cases=covid_cases, flu_cases=flu_cases)
        db.add(record)
    else:
        if covid_cases is not None:
            record.covid_cases = covid_cases
        if flu_cases is not None:
            record.flu_cases = flu_cases
    db.commit()
    db.refresh(record)
    return record


def get_cases(
    db: Session,
    start_date: Optional[Date] = None,
    end_date: Optional[Date] = None,
) -> list[CaseRecord]:
    query = db.query(CaseRecord)
    if start_date:
        query = query.filter(CaseRecord.date >= start_date)
    if end_date:
        query = query.filter(CaseRecord.date <= end_date)
    return query.order_by(CaseRecord.date).all()
