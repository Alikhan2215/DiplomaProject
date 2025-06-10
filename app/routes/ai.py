from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from bson import ObjectId
from datetime import datetime
from pathlib import Path

from app.schemas.ai import SummarizeIn, SummarizeOut
from app.core.security import get_current_user
from app.core.db import db
from app.utils.file_utils import extract_text
from app.services.ai_service import summarize_text

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/summarize", response_model=SummarizeOut)
async def ai_summarize(
    req: SummarizeIn,
    folder_id: str | None = None,
    user=Depends(get_current_user)
):
    # 1) Fetch the already-uploaded document
    doc = await db.documents.find_one({
        "_id": ObjectId(req.doc_id),
        "user_email": user["email"]
    })
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2) Extract text (including tables)
    text = extract_text(Path(doc["path"]))
    if not text:
        raise HTTPException(status_code=400, detail="No extractable text in document")

    # 3) Generate summary off the event loop
    summary = await run_in_threadpool(summarize_text, text, req.mode.value)

    # 4) Persist it, optionally assigning to a folder
    created_at = datetime.utcnow()
    rec = {
        "doc_id": ObjectId(req.doc_id),
        "user_email": user["email"],
        "filename": doc["filename"],
        "mode": req.mode.value,
        "summary": summary,
        "created_at": created_at,
    }
    if folder_id:
        try:
            rec["folder_id"] = ObjectId(folder_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid folder_id")

    result = await db.summaries.insert_one(rec)

    # 5) Return it
    return SummarizeOut(
        id=str(result.inserted_id),
        doc_id=req.doc_id,
        filename=doc["filename"],
        mode=req.mode,
        summary=summary,
        created_at=created_at,
        folder_id=folder_id
    )
