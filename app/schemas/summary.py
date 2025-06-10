from pydantic import BaseModel

class SummaryFolderUpdate(BaseModel):
    folder_id: str | None  # assign to folder (or null to un‐assign)
