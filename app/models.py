from sqlalchemy import Column, Date, Integer
from app.database import Base


class CaseRecord(Base):
    """One row per weekly reporting period."""

    __tablename__ = "case_records"

    date = Column(Date, primary_key=True, index=True)
    covid_cases = Column(Integer, nullable=True)
    flu_cases = Column(Integer, nullable=True)
