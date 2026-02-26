from datetime import date as Date
from typing import Optional
from pydantic import BaseModel


class CaseRecordOut(BaseModel):
    date: Date
    covid_cases: Optional[int] = None
    flu_cases: Optional[int] = None

    model_config = {"from_attributes": True}
