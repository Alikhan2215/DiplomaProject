# app/models/document.py

from pydantic import BaseModel
from datetime import datetime

class DocumentOut(BaseModel):
    id: str
    filename: str
    upload_date: datetime

