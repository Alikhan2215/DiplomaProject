# app/schemas/folder.py

from pydantic import BaseModel
from datetime import datetime

class FolderCreate(BaseModel):
    name: str

class FolderOut(BaseModel):
    id: str            # no alias, just a plain string
    name: str
    created_at: datetime
