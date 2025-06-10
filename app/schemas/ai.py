# app/schemas/ai.py

from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class SummaryMode(str, Enum):
    concise  = "concise"
    standard = "standard"
    detailed = "detailed"

class SummarizeIn(BaseModel):
    doc_id: str
    mode: SummaryMode = SummaryMode.standard

class SummarizeOut(BaseModel):
    id: str            # drop alias
    doc_id: str
    filename: str
    mode: SummaryMode
    summary: str
    created_at: datetime
    folder_id: str | None = None
    note: str | None = None