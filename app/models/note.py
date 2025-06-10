from pydantic import BaseModel

class SummaryNoteUpdate(BaseModel):
    note: str